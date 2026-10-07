#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(overlap)
  library(sp)
  library(jsonlite)
  library(digest)
})

args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(flag) {
  i <- match(flag, args)
  if (is.na(i) || i == length(args)) stop(paste("missing", flag))
  args[[i + 1]]
}

input_root <- get_arg("--input-root")
header_contract_path <- get_arg("--header-contract")
model_contract_path <- get_arg("--model-contract")
out_path <- get_arg("--out")

header_contract <- fromJSON(header_contract_path, simplifyVector = FALSE)
model_contract <- fromJSON(model_contract_path, simplifyVector = FALSE)

if (model_contract$contract_id != "e5-wildpig-activity-anchor-transfer-model-v1") {
  stop("unexpected model contract")
}
if (header_contract$source$pinned_commit != "bc97ff80ec91aba03f58f06629c7e8dfff9eb85d") {
  stop("source commit drift")
}

floor_eps <- as.numeric(model_contract$preprocessing$circular_density$positivity_floor)
seasons <- c("spring", "summer", "fall", "winter")
geographies <- c("FL", "CA")

site_meta <- list(
  FL = list(tz="America/New_York", lon=-81.195665, lat=27.168992),
  CA = list(tz="America/Los_Angeles", lon=-118.7832222, lat=34.898505)
)

seed_from_key <- function(key) {
  h <- digest(key, algo="sha256", serialize=FALSE)
  as.integer(strtoi(substr(h, 1, 7), base=16L))
}

normalize_vec <- function(x) {
  x <- as.numeric(x)
  x[!is.finite(x)] <- 0
  x <- pmax(x, floor_eps)
  x / sum(x)
}

circular_density <- function(times) {
  times <- as.numeric(times)
  times <- times[is.finite(times)]
  if (length(times) < 2) stop("insufficient times for circular density")
  y <- overlap::densityPlot(times, xscale=1, n.grid=256, extend=NULL)$y
  if (length(y) < 2) stop("densityPlot returned insufficient grid")
  y <- y[1:(length(y)-1)]
  normalize_vec(y)
}

parse_datetime <- function(x, tz) {
  fmts <- c(
    "%Y/%m/%d %H:%M",
    "%Y/%m/%d %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S"
  )
  out <- rep(as.POSIXct(NA, tz=tz), length(x))
  remaining <- seq_along(x)
  for (fmt in fmts) {
    if (length(remaining) == 0) break
    parsed <- as.POSIXct(strptime(as.character(x[remaining]), fmt, tz=tz))
    good <- which(!is.na(parsed))
    if (length(good)) {
      out[remaining[good]] <- parsed[good]
      remaining <- remaining[-good]
    }
  }
  out
}

clock_rad_from_posix <- function(x, tz) {
  lt <- as.POSIXlt(x, tz=tz)
  sec <- lt$hour * 3600 + lt$min * 60 + lt$sec
  (sec / 86400) * 2 * pi
}

site_coords <- function(meta) {
  sp::SpatialPoints(
    cbind(meta$lon, meta$lat),
    proj4string=sp::CRS("+proj=longlat +datum=WGS84")
  )
}

gps_individual_kernels <- function(df, geography, season) {
  meta <- site_meta[[geography]]
  if (!all(c("Indiv_ID", "Fix_DateTime", "X", "Y") %in% names(df))) {
    stop(paste("GPS schema mismatch", geography, season))
  }
  df$Indiv_ID <- as.character(df$Indiv_ID)
  df$FixParsed <- parse_datetime(df$Fix_DateTime, meta$tz)
  df$X <- as.numeric(df$X)
  df$Y <- as.numeric(df$Y)
  df <- df[!is.na(df$Indiv_ID) & !is.na(df$FixParsed) & is.finite(df$X) & is.finite(df$Y), ]
  ids <- unique(df$Indiv_ID)
  kernels <- list()
  set.seed(seed_from_key(paste0(
    model_contract$provenance$source_commit, ":", geography, ":", season
  )))
  coords <- site_coords(meta)

  for (id in ids) {
    z <- df[df$Indiv_ID == id, ]
    z <- z[order(z$FixParsed), ]
    if (nrow(z) < 2) next
    dtsec <- as.numeric(diff(z$FixParsed), units="secs")
    dx <- diff(z$X)
    dy <- diff(z$Y)
    dist <- sqrt(dx^2 + dy^2)
    dtmin <- dtsec / 60
    dthr <- dtsec / 3600
    meterph <- round(dist / dthr, digits=0)
    valid <- which(is.finite(dtmin) & dtmin > 19 & dtmin < 41 &
                   is.finite(meterph) & meterph > 0)
    if (!length(valid)) next

    pieces <- vector("list", length(valid))
    for (k in seq_along(valid)) {
      j <- valid[[k]]
      n <- as.integer(meterph[[j]])
      if (n <= 0) next
      offsets <- sort(runif(n, 0, dtsec[[j]]))
      pieces[[k]] <- z$FixParsed[[j]] + offsets
    }
    pseudo <- do.call(c, pieces)
    if (is.null(pseudo) || length(pseudo) < 2) next
    pseudo <- as.POSIXct(pseudo, origin="1970-01-01", tz=meta$tz)
    clock <- clock_rad_from_posix(pseudo, meta$tz)
    sun <- overlap::sunTime(clockTime=clock, Dates=pseudo, Coords=coords)
    kernels[[id]] <- circular_density(sun)
  }
  if (!length(kernels)) stop(paste("no viable GPS individuals", geography, season))
  mat <- do.call(cbind, kernels)
  list(
    kernels=mat,
    point=normalize_vec(rowMeans(mat)),
    n_individuals=ncol(mat)
  )
}

camera_site_times <- function(df, geography, season) {
  meta <- site_meta[[geography]]
  if (!all(c("LocationName", "timeRad", "ImageDate") %in% names(df))) {
    stop(paste("camera schema mismatch", geography, season))
  }
  dates <- as.POSIXct(strptime(as.character(df$ImageDate), "%m/%d/%Y", tz=meta$tz))
  clock <- as.numeric(df$timeRad)
  keep <- !is.na(dates) & is.finite(clock) & !is.na(df$LocationName)
  if (!any(keep)) stop(paste("no viable camera events", geography, season))
  coords <- site_coords(meta)
  sun <- overlap::sunTime(clockTime=clock[keep], Dates=dates[keep], Coords=coords)
  loc <- as.character(df$LocationName[keep])
  split_times <- split(as.numeric(sun), loc)
  split_times <- split_times[vapply(split_times, length, integer(1)) > 0]
  if (!length(split_times)) stop("no camera sites after split")
  pooled <- unlist(split_times, use.names=FALSE)
  list(
    site_times=split_times,
    point=circular_density(pooled),
    n_sites=length(split_times),
    n_events=length(pooled)
  )
}

recover_D <- function(A, C) {
  A <- normalize_vec(A)
  C <- normalize_vec(C)
  z <- log(C) - log(A)
  exp(z - mean(z))
}

predict_camera <- function(A, D) {
  normalize_vec(normalize_vec(A) * as.numeric(D))
}

overlap_coef <- function(p, q) {
  p <- normalize_vec(p)
  q <- normalize_vec(q)
  sum(pmin(p, q))
}

specs <- header_contract$source$seasonal_files
cells <- setNames(vector("list", length(geographies)), geographies)
for (g in geographies) cells[[g]] <- setNames(vector("list", length(seasons)), seasons)

for (g in geographies) {
  for (s in seasons) {
    gps_spec <- Filter(function(x) x$geography == g && x$method == "gps" && x$season == s, specs)
    cam_spec <- Filter(function(x) x$geography == g && x$method == "camera" && x$season == s, specs)
    if (length(gps_spec) != 1 || length(cam_spec) != 1) stop("input manifest mismatch")
    gps_path <- file.path(input_root, gps_spec[[1]]$path)
    cam_path <- file.path(input_root, cam_spec[[1]]$path)
    gps_df <- read.csv(gps_path, stringsAsFactors=FALSE, check.names=TRUE)
    cam_df <- read.csv(cam_path, stringsAsFactors=FALSE, check.names=TRUE)
    cells[[g]][[s]] <- list(
      gps=gps_individual_kernels(gps_df, g, s),
      cam=camera_site_times(cam_df, g, s)
    )
  }
}

transfer_rows <- function(cellset) {
  rows <- list()
  k <- 1
  for (train in geographies) {
    held <- setdiff(geographies, train)
    for (s in seasons) {
      A_train <- cellset[[train]][[s]]$gps$point
      C_train <- cellset[[train]][[s]]$cam$point
      D_train <- recover_D(A_train, C_train)
      A_held <- cellset[[held]][[s]]$gps$point
      C_held <- cellset[[held]][[s]]$cam$point
      pred <- predict_camera(A_held, D_train)
      corrected <- overlap_coef(pred, C_held)
      baseline <- overlap_coef(A_held, C_held)
      rows[[k]] <- list(
        training_geography=train,
        heldout_geography=held,
        season=s,
        baseline_overlap=baseline,
        corrected_overlap=corrected,
        gain=corrected-baseline
      )
      k <- k + 1
    }
  }
  rows
}

point_transfers <- transfer_rows(cells)
point_gains <- vapply(point_transfers, function(x) x$gain, numeric(1))

bootstrap_gains <- matrix(NA_real_, nrow=1000, ncol=8)
colnames(bootstrap_gains) <- vapply(
  point_transfers,
  function(x) paste(x$training_geography, x$heldout_geography, x$season, sep="_"),
  character(1)
)

for (b in 1:1000) {
  set.seed(seed_from_key(paste0(
    model_contract$contract_id, ":", b
  )))
  boot <- setNames(vector("list", length(geographies)), geographies)
  for (g in geographies) {
    boot[[g]] <- setNames(vector("list", length(seasons)), seasons)
    for (s in seasons) {
      cell <- cells[[g]][[s]]
      kmat <- cell$gps$kernels
      gi <- sample(seq_len(ncol(kmat)), size=ncol(kmat), replace=TRUE)
      A <- normalize_vec(rowMeans(kmat[, gi, drop=FALSE]))

      st <- cell$cam$site_times
      si <- sample(seq_along(st), size=length(st), replace=TRUE)
      cam_times <- unlist(st[si], use.names=FALSE)
      C <- circular_density(cam_times)

      boot[[g]][[s]] <- list(
        gps=list(point=A),
        cam=list(point=C)
      )
    }
  }
  trs <- transfer_rows(boot)
  bootstrap_gains[b,] <- vapply(trs, function(x) x$gain, numeric(1))
}

median_boot <- apply(bootstrap_gains, 1, median)
ci_fun <- function(x) as.numeric(quantile(x, probs=c(0.025,0.975), na.rm=TRUE, names=FALSE))
median_ci <- ci_fun(median_boot)

transfer_summaries <- vector("list", ncol(bootstrap_gains))
for (j in seq_len(ncol(bootstrap_gains))) {
  ci <- ci_fun(bootstrap_gains[,j])
  transfer_summaries[[j]] <- c(
    point_transfers[[j]],
    list(bootstrap_ci_lower=ci[[1]], bootstrap_ci_upper=ci[[2]])
  )
}

interpretation <- if (median_ci[[1]] > 0) {
  "SUPPORTED"
} else if (median_ci[[2]] < 0) {
  "CONTRADICTED"
} else {
  "UNRESOLVED"
}

cell_counts <- list()
for (g in geographies) {
  for (s in seasons) {
    cell_counts[[paste(g,s,sep="_")]] <- list(
      gps_individuals=cells[[g]][[s]]$gps$n_individuals,
      camera_sites=cells[[g]][[s]]$cam$n_sites,
      camera_events=cells[[g]][[s]]$cam$n_events
    )
  }
}

result <- list(
  schema_version=1,
  programme_id="E5_INDEPENDENT_ACTIVITY_DETECTION",
  candidate_id="wolfson_wildpig_gps_camera_2015_2018",
  route_id="e5-external-activity-anchor-v1",
  result_id="e5-wildpig-activity-anchor-transfer-result-v1",
  status=interpretation,
  source_commit=header_contract$source$pinned_commit,
  route_boundary=list(
    original_G4_passed=FALSE,
    absolute_detection_probability_identified=FALSE,
    abundance_identified=FALSE,
    causal_sensor_mechanism_identified=FALSE,
    untouched_preregistration=FALSE
  ),
  observed_sample_structure=cell_counts,
  point_transfers=transfer_summaries,
  primary_summary=list(
    point_median_gain=median(point_gains),
    point_minimum_gain=min(point_gains),
    point_positive_gain_count=sum(point_gains > 0),
    total_transfers=length(point_gains),
    bootstrap_median_gain_ci_lower=median_ci[[1]],
    bootstrap_median_gain_ci_upper=median_ci[[2]],
    interpretation=interpretation
  ),
  bootstrap=list(
    replicates=1000,
    gps_resampling_unit="individual",
    camera_resampling_unit="LocationName",
    percentile_interval=c(0.025,0.975)
  ),
  claim_boundary=list(
    maximum_claim="relative diel camera observation distortion transfer under an external GPS activity anchor",
    original_E5_G4_pass_claim=FALSE,
    absolute_detection_claim=FALSE,
    abundance_claim=FALSE,
    causal_sensor_mechanism_claim=FALSE
  )
)

dir.create(dirname(out_path), recursive=TRUE, showWarnings=FALSE)
writeLines(toJSON(result, pretty=TRUE, auto_unbox=TRUE, digits=16), out_path)

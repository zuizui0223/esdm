# First external botanical source pilot: Costa Rica only
# Source: BIEN R package, plot-country API; never GBIF occurrence.
# A source-level independence decision requires manual verification.
suppressPackageStartupMessages(library(BIEN))
suppressPackageStartupMessages(library(jsonlite))
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) stop("usage: Rscript pilot.R manifest.json output.json")
manifest <- fromJSON(args[[1]], simplifyVector = TRUE)
stopifnot(length(manifest$plant_taxa) == 106L,
          "CR" %in% manifest$shadow_fitted_countries)
status <- list(schema_version = 1L, source = "BIEN_plot_country",
               country = "Costa Rica", country_code = "CR",
               source_version = tryCatch(as.character(BIEN_metadata_database_version()),
                                         error = function(e) paste("UNAVAILABLE:", conditionMessage(e))),
               original_106_taxa = 106L,
               external_plot_rows_read = 0L,
               external_plot_species_exact_matches = NULL,
               independent_source_verified = FALSE,
               status = "NOT_EVALUABLE",
               plot_absence_inferred = FALSE,
               fruit_resource_estimated = FALSE,
               bat_model_fitted = FALSE)
save_receipt <- function() {
  dir.create(dirname(args[[2]]), recursive = TRUE, showWarnings = FALSE)
  write_json(status, args[[2]], pretty = TRUE, auto_unbox = TRUE, null = "null")
}
d <- tryCatch(
  BIEN_plot_country(country = "Costa Rica", all.metadata = TRUE,
                    cultivated = FALSE, natives.only = TRUE),
  error = function(e) e
)
if (inherits(d, "error")) {
  status$status <- "BIEN_PLOT_COUNTRY_SOURCE_STOP"
  status$error <- conditionMessage(d)
} else if (!is.data.frame(d)) {
  status$status <- "BIEN_UNEXPECTED_RESPONSE_STOP"
} else {
  status$external_plot_rows_read <- nrow(d)
  status$returned_column_names <- names(d)
  # Never infer taxonomy, source identity, or plot independence from unnamed columns.
  candidates <- c("scrubbed_species_binomial", "scrubbed_species", "species")
  taxon_col <- candidates[candidates %in% names(d)]
  if (length(taxon_col) == 0L) {
    status$status <- "BIEN_TAXON_SCHEMA_STOP"
  } else {
    taxon_col <- taxon_col[[1]]
    matched <- sort(intersect(unique(as.character(d[[taxon_col]])), manifest$plant_taxa))
    status$taxon_column_used <- taxon_col
    status$external_plot_species_exact_matches <- length(matched)
    status$matched_species_names <- matched
    # The BIEN hierarchy is datasource > dataset > plot_name. Never use plot_name alone.
    # A unique hierarchical label is not independent sampling without source review.
    complete_distinct <- function(tbl, keys) {
      if (!all(keys %in% names(tbl))) return(NULL)
      x <- tbl[, keys, drop = FALSE]
      valid <- rep(TRUE, nrow(x))
      for (key in keys) {
        v <- as.character(x[[key]])
        valid <- valid & !is.na(v) & nzchar(trimws(v))
      }
      nrow(unique(x[valid, , drop = FALSE]))
    }
    present_n <- function(x) {
      if (is.null(x)) return(NULL)
      v <- as.character(x)
      sum(!is.na(v) & nzchar(trimws(v)))
    }
    matched_rows <- d[!is.na(d[[taxon_col]]) &
                      as.character(d[[taxon_col]]) %in% matched, , drop = FALSE]
    status$source_selection <- list(natives_only = TRUE, cultivated = FALSE,
                                    taxon_match = "exact_scrubbed_binomial")
    status$matched_record_rows <- nrow(matched_rows)
    status$total_complete_hierarchical_plot_labels <- complete_distinct(
      d, c("datasource", "dataset", "plot_name"))
    status$matched_complete_hierarchical_plot_labels <- complete_distinct(
      matched_rows, c("datasource", "dataset", "plot_name"))
    status$matched_complete_hierarchical_datasets <- complete_distinct(
      matched_rows, c("datasource", "dataset"))
    status$matched_datasource_labels <- complete_distinct(
      matched_rows, "datasource")
    status$matched_source_id_values <- complete_distinct(
      matched_rows, "datasource_id")
    status$matched_rows_with_sampling_protocol <- if ("sampling_protocol" %in% names(d))
      present_n(matched_rows$sampling_protocol) else NULL
    status$matched_rows_with_collection_date <- if ("date_collected" %in% names(d))
      present_n(matched_rows$date_collected) else NULL
    status$matched_rows_with_positive_plot_area <- if ("plot_area_ha" %in% names(d)) {
      v <- suppressWarnings(as.numeric(as.character(matched_rows$plot_area_ha)))
      sum(is.finite(v) & v > 0)
    } else NULL
    status$matched_rows_with_positive_individual_count <- if ("individual_count" %in% names(d)) {
      v <- suppressWarnings(as.numeric(as.character(matched_rows$individual_count)))
      sum(is.finite(v) & v > 0)
    } else NULL
    # Counts of positive plot records, not surveyed absence or fruit biomass.
    status$per_matched_taxon <- lapply(matched, function(sp) {
      q <- matched_rows[as.character(matched_rows[[taxon_col]]) == sp, , drop = FALSE]
      list(taxon = sp, record_rows = nrow(q),
           unique_datasource_labels = complete_distinct(q, "datasource"),
           unique_hierarchical_datasets = complete_distinct(q, c("datasource", "dataset")),
           unique_hierarchical_plots = complete_distinct(q, c("datasource", "dataset", "plot_name")))
    })
    status$independent_source_verified <- FALSE
    status$survey_absence_available <- FALSE
    status$fruit_resource_estimated <- FALSE
    status$bat_model_fitted <- FALSE
    status$status <- "EXPLORATORY_PLOT_COUNTRY_EXACT_TAXON_COVERAGE_ONLY"
  }
}

save_receipt()

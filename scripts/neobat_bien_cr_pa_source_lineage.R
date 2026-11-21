# Source-level provenance registry for two ALREADY-opened native-only BIEN plot pilots.
# Query original plot source once per country; never archive row-level coordinates.
suppressPackageStartupMessages(library(BIEN))
suppressPackageStartupMessages(library(jsonlite))
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 4L) stop("usage: Rscript lineage.R manifest.json CR|PA 'Country Name' out.json")
manifest <- fromJSON(args[[1]], simplifyVector = TRUE)
country_code <- args[[2]]
country_name <- args[[3]]
if (country_code != "CR" && country_code != "PA") stop("only frozen prior BIEN pilots permitted")
if ((country_code == "CR" && country_name != "Costa Rica") ||
    (country_code == "PA" && country_name != "Panama")) stop("country code/name mismatch")
stopifnot(length(manifest$plant_taxa) == 106L,
          country_code %in% manifest$shadow_fitted_countries)
receipt <- list(
  schema_version = 1L, status = "NOT_EVALUABLE",
  source = "BIEN_plot_country",
  country = country_name, country_code = country_code,
  BIEN_database_version = tryCatch(as.character(BIEN_metadata_database_version()),
                                   error = function(e) paste("UNAVAILABLE:", conditionMessage(e))),
  source_query = list(all_metadata=TRUE, natives_only=TRUE, cultivated=FALSE),
  original_fixed_plant_denominator = 106L,
  matched_plant_species = NULL, matched_plant_row_count = NULL,
  matched_primary_dataset_registry = NULL,
  original_primary_source_independence_verified = FALSE,
  disjoint_from_GBIF_plant_dataset_keys_verified = FALSE,
  absent_species_inferred = FALSE, fruit_resource_estimated = FALSE,
  bat_model_fitted = FALSE
)
save_receipt <- function() {
  dir.create(dirname(args[[4]]), recursive=TRUE, showWarnings=FALSE)
  write_json(receipt, args[[4]], pretty=TRUE, auto_unbox=TRUE, null="null")
}
response <- tryCatch(
  BIEN_plot_country(country=country_name, all.metadata=TRUE,
                    natives.only=TRUE, cultivated=FALSE),
  error=function(e) e)
if (inherits(response,"error")) {
  receipt$status <- "BIEN_SOURCE_ERROR_STOP"
  receipt$error <- conditionMessage(response)
} else if (!is.data.frame(response)) {
  receipt$status <- "BIEN_NON_TABLE_STOP"
} else {
  d <- response
  required <- c("scrubbed_species_binomial", "datasource", "dataset", "datasource_id", "plot_name")
  receipt$total_plot_taxon_record_rows <- nrow(d)
  receipt$metadata_column_names <- names(d)
  if (!all(required %in% names(d))) {
    receipt$status <- "BIEN_METADATA_SCHEMA_STOP"
    receipt$missing_fields <- setdiff(required,names(d))
  } else {
    sp <- as.character(d$scrubbed_species_binomial)
    keep <- !is.na(sp) & sp %in% manifest$plant_taxa
    hit <- d[keep, , drop=FALSE]
    receipt$matched_plant_species <- length(unique(sp[keep]))
    receipt$matched_plant_row_count <- nrow(hit)
    missing_marker <- "[MISSING]"
    clean <- function(v) {
      x <- trimws(as.character(v))
      x[is.na(x) | !nzchar(x)] <- missing_marker
      x
    }
    if (nrow(hit)) {
      src <- clean(hit$datasource)
      dataset <- clean(hit$dataset)
      sid <- clean(hit$datasource_id)
      unique_key <- paste(src,dataset,sid,sep="::[source-break]::")
      groups <- split(seq_len(nrow(hit)), unique_key)
      reg <- lapply(groups,function(idx) {
        q <- hit[idx,,drop=FALSE]
        lab <- paste(clean(q$datasource),clean(q$dataset),
                     clean(q$plot_name),sep="::[plot-break]::")
        # Label counts are not validated geographic or statistical independence.
        list(datasource_label=src[[idx[[1]]]],
             dataset_label=dataset[[idx[[1]]]],
             datasource_id=sid[[idx[[1]]]],
             provenance_label_complete=all(src[idx] != missing_marker &
                                            dataset[idx] != missing_marker &
                                            sid[idx] != missing_marker),
             matched_record_rows=nrow(q),
             matched_taxa=length(unique(as.character(q$scrubbed_species_binomial))),
             distinct_nested_plot_labels=length(unique(lab[
               clean(q$plot_name) != missing_marker ])))
      })
      receipt$matched_primary_dataset_registry <- unname(reg)
      receipt$registry_group_count <- length(reg)
      receipt$source_label_or_id_missing_rows <- sum(src == missing_marker |
                                                      dataset == missing_marker |
                                                      sid == missing_marker)
    } else {
      receipt$matched_primary_dataset_registry <- list()
      receipt$registry_group_count <- 0L
      receipt$source_label_or_id_missing_rows <- 0L
    }
    receipt$status <- "EXPLORATORY_SOURCE_LABEL_REGISTRY_ONLY"
  }
}
save_receipt()

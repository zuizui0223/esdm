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
    status$status <- "EXPLORATORY_PLOT_COUNTRY_EXACT_TAXON_COVERAGE_ONLY"
  }
}

save_receipt()

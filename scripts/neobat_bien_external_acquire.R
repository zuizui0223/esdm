# Official BIEN CR/PA acquisition for the already-frozen external diagnostic.
# Complete returned rows go only to a private temporary JSON; public output is
# aggregate coverage and explicitly selected datasource bibliography fields.

FIXED106_SHA256 <- "41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6"
COUNTRY_NAMES <- c(CR="Costa Rica", PA="Panama")
FIXED_SOURCE_IDS <- c(18L, 27L, 37L, 40L, 59L, 66L)
REQUIRED_PLOT_COLUMNS <- c(
  "country", "plot_name", "subplot", "plot_area_ha", "sampling_protocol",
  "scrubbed_species_binomial", "individual_count", "latitude", "longitude",
  "date_collected", "datasource", "dataset", "datasource_id",
  "coord_uncertainty_m", "methodology_reference", "methodology_description",
  "growth_forms_included_all", "growth_forms_included_trees",
  "growth_forms_included_shrubs", "growth_forms_included_lianas",
  "growth_forms_included_herbs", "growth_forms_included_epiphytes",
  "growth_forms_included_notes", "taxa_included_all", "taxa_included_seed_plants",
  "taxa_included_ferns_lycophytes", "taxa_included_bryophytes", "taxa_included_exclusions"
)
REQUIRED_SOURCE_COLUMNS <- c("datasource_id", "source_name", "source_fullname",
                             "proximate_provider_datasource_id", "source_citation")
SAFE_SOURCE_COLUMNS <- c(
  REQUIRED_SOURCE_COLUMNS, "source_url", "source_uri", "source_website",
  "url", "url_source", "website", "doi", "source_doi", "dataset_doi",
  "source_license", "license", "licence", "license_url", "licence_url",
  "access_conditions", "terms_of_use", "citation_bibtex"
)

abort_acquisition <- function(code) {
  stop(structure(list(message=code, call=NULL),
                 class=c("neobat_acquisition_error", "error", "condition")))
}

parse_arguments <- function(args) {
  expected <- c("--private-output", "--receipt-output", "--manifest")
  if (length(args) != 6L || anyDuplicated(args[c(1, 3, 5)]) ||
      !setequal(args[c(1, 3, 5)], expected) || any(!nzchar(args[c(2, 4, 6)]))) {
    abort_acquisition("USAGE_PRIVATE_OUTPUT_RECEIPT_OUTPUT_MANIFEST_REQUIRED")
  }
  setNames(as.list(args[c(2, 4, 6)]), sub("^--", "", args[c(1, 3, 5)]))
}

present <- function(x) !is.na(x) & nzchar(trimws(as.character(x)))
numeric_values <- function(x) suppressWarnings(as.numeric(as.character(x)))
distinct_present <- function(x) length(unique(as.character(x)[present(x)]))

complete_key_count <- function(d, columns) {
  if (!nrow(d)) return(0L)
  ok <- rep(TRUE, nrow(d))
  for (column in columns) ok <- ok & present(d[[column]])
  nrow(unique(d[ok, columns, drop=FALSE]))
}

coverage_counts <- function(d) {
  uncertainty <- numeric_values(d$coord_uncertainty_m)
  lat <- numeric_values(d$latitude)
  lon <- numeric_values(d$longitude)
  method_any <- present(d$sampling_protocol) | present(d$methodology_reference) |
                present(d$methodology_description)
  list(
    rows_with_missing_species_label=sum(!present(d$scrubbed_species_binomial)),
    rows_with_missing_datasource_id=sum(!present(d$datasource_id)),
    rows_with_missing_datasource_label=sum(!present(d$datasource)),
    rows_with_missing_dataset_label=sum(!present(d$dataset)),
    rows_with_missing_plot_label=sum(!present(d$plot_name)),
    rows_with_date_collected=sum(present(d$date_collected)),
    rows_with_sampling_protocol=sum(present(d$sampling_protocol)),
    rows_with_methodology_reference=sum(present(d$methodology_reference)),
    rows_with_methodology_description=sum(present(d$methodology_description)),
    rows_with_any_method_field=sum(method_any),
    rows_with_missing_all_method_fields=sum(!method_any),
    rows_with_uncertainty_value=sum(present(d$coord_uncertainty_m)),
    rows_with_finite_nonnegative_uncertainty=sum(is.finite(uncertainty) & uncertainty >= 0),
    rows_with_known_uncertainty_le12500m=sum(is.finite(uncertainty) & uncertainty >= 0 & uncertainty <= 12500),
    rows_with_known_uncertainty_gt12500m=sum(is.finite(uncertainty) & uncertainty > 12500),
    rows_with_invalid_nonmissing_uncertainty=sum(present(d$coord_uncertainty_m) & (!is.finite(uncertainty) | uncertainty < 0)),
    rows_with_valid_geographic_coordinates=sum(is.finite(lat) & is.finite(lon) & abs(lat) <= 90 & abs(lon) <= 180),
    rows_with_positive_plot_area=sum(is.finite(numeric_values(d$plot_area_ha)) & numeric_values(d$plot_area_ha) > 0),
    rows_with_positive_individual_count=sum(is.finite(numeric_values(d$individual_count)) & numeric_values(d$individual_count) > 0)
  )
}

summarize_country <- function(d, taxa, code) {
  species <- as.character(d$scrubbed_species_binomial)
  hit <- !is.na(species) & species %in% taxa
  focal <- d[hit, , drop=FALSE]
  prior <- list(CR=list(total_rows=21949L, matched_taxa=17L, focal_record_rows=557L),
                PA=list(total_rows=8390L, matched_taxa=22L, focal_record_rows=974L))[[code]]
  list(
    country_code=code, country=unname(COUNTRY_NAMES[[code]]),
    total_rows=nrow(d), matched_taxa=length(unique(species[hit])),
    focal_record_rows=sum(hit), fixed_taxon_denominator=length(taxa),
    previous_acquisition_counts=prior,
    observed_minus_previous=list(total_rows=nrow(d)-prior$total_rows,
                                 matched_taxa=length(unique(species[hit]))-prior$matched_taxa,
                                 focal_record_rows=sum(hit)-prior$focal_record_rows),
    previous_counts_are_reported_not_enforced_as_selection_rules=TRUE,
    matched_taxon_names=sort(unique(species[hit]), method="radix"),
    focal_record_counts=setNames(as.list(vapply(taxa, function(sp) sum(species == sp, na.rm=TRUE), integer(1))), taxa),
    returned_column_names=names(d),
    complete_source_dataset_count=complete_key_count(d, c("datasource_id", "datasource", "dataset")),
    distinct_datasource_id_count=distinct_present(d$datasource_id),
    distinct_datasource_label_count=distinct_present(d$datasource),
    complete_hierarchical_plot_label_count=complete_key_count(d, c("datasource_id", "datasource", "dataset", "plot_name")),
    focal_distinct_datasource_id_count=distinct_present(focal$datasource_id),
    focal_datasource_ids=sort(unique(as.character(focal$datasource_id)[present(focal$datasource_id)])),
    coverage_all=coverage_counts(d), coverage_focal=coverage_counts(focal),
    record_rows_are_not_independent_sites=TRUE,
    unobserved_taxa_are_not_absent=TRUE,
    equal_metadata_does_not_establish_equal_effort=TRUE
  )
}

source_metadata_columns <- function(available) {
  if (!all(REQUIRED_SOURCE_COLUMNS %in% available)) {
    abort_acquisition("BIEN_DATASOURCE_SCHEMA_MISSING_REQUIRED_COLUMNS")
  }
  SAFE_SOURCE_COLUMNS[SAFE_SOURCE_COLUMNS %in% available]
}

source_metadata_query <- function(columns) {
  if (!length(columns) || any(!columns %in% SAFE_SOURCE_COLUMNS)) {
    abort_acquisition("UNSAFE_DATASOURCE_COLUMN_SELECTION")
  }
  selected <- paste(sprintf('"%s"', columns), collapse=", ")
  fixed <- paste(FIXED_SOURCE_IDS, collapse=", ")
  paste0("SELECT ", selected, " FROM datasource WHERE datasource_id IN (", fixed,
         ") OR datasource_id IN (SELECT proximate_provider_datasource_id FROM datasource ",
         "WHERE datasource_id IN (", fixed, ")) ORDER BY datasource_id;")
}

clean_public_source_text <- function(x) {
  value <- as.character(x)
  value <- gsub("(https?://)[^/[:space:]@]+@", "\\1", value,
                ignore.case=TRUE, perl=TRUE)
  value <- gsub("[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}",
                "[REDACTED_EMAIL]", value, ignore.case=TRUE, perl=TRUE)
  value <- gsub("([?&](?:token|api_key|password|signature|credential)=)[^&#[:space:]]+",
                "\\1[REDACTED]", value, ignore.case=TRUE, perl=TRUE)
  value
}

quiet_query <- function(fun, code) {
  result <- tryCatch(suppressMessages(suppressWarnings(fun())),
                     error=function(e) abort_acquisition(code))
  if (!is.data.frame(result)) abort_acquisition(code)
  result
}

fetch_source_bibliography <- function(sql_query) {
  # Schema names only. This does not select contact or authentication values.
  schema_query <- paste(
    "SELECT a.attname AS column_name FROM pg_catalog.pg_attribute a",
    "WHERE a.attrelid=to_regclass('datasource') AND a.attnum>0",
    "AND NOT a.attisdropped ORDER BY a.attnum;"
  )
  schema <- quiet_query(function() sql_query(schema_query), "BIEN_DATASOURCE_SCHEMA_QUERY_FAILED")
  if (!"column_name" %in% names(schema) || !nrow(schema)) {
    abort_acquisition("BIEN_DATASOURCE_SCHEMA_EMPTY")
  }
  available <- as.character(schema$column_name)
  selected <- source_metadata_columns(available)
  sources <- quiet_query(function() sql_query(source_metadata_query(selected)),
                         "BIEN_DATASOURCE_BIBLIOGRAPHY_QUERY_FAILED")
  if (!identical(names(sources), selected)) abort_acquisition("BIEN_DATASOURCE_RETURNED_SCHEMA_DRIFT")
  ids <- as.character(sources$datasource_id)
  if (anyNA(ids) || anyDuplicated(ids) || !all(as.character(FIXED_SOURCE_IDS) %in% ids)) {
    abort_acquisition("BIEN_FIXED_DATASOURCE_UNIVERSE_DRIFT")
  }
  original <- sources[ids %in% as.character(FIXED_SOURCE_IDS), , drop=FALSE]
  proximate <- as.character(original$proximate_provider_datasource_id)
  proximate <- unique(proximate[present(proximate)])
  if (!all(proximate %in% ids)) abort_acquisition("BIEN_PROXIMATE_PROVIDER_ROW_MISSING")
  if (!setequal(ids, union(as.character(FIXED_SOURCE_IDS), proximate))) {
    abort_acquisition("BIEN_DATASOURCE_QUERY_UNIVERSE_DRIFT")
  }
  # Values from bibliography columns only. Do not pass through SELECT * data.
  for (column in selected) {
    sources[[column]] <- clean_public_source_text(sources[[column]])
  }
  list(
    fixed_datasource_ids=as.list(FIXED_SOURCE_IDS),
    proximate_provider_datasource_ids=as.list(sort(proximate)),
    available_column_names=available,
    selected_public_column_names=selected,
    source_rows=sources,
    fixed_sources_with_nonempty_citation=sum(present(original$source_citation)),
    contact_or_credential_columns_queried=FALSE,
    source_independence_from_original_GBIF="UNKNOWN"
  )
}

validate_manifest <- function(manifest) {
  taxa <- manifest$plant_taxa
  if (!is.character(taxa) || length(taxa) != 106L || anyNA(taxa) ||
      anyDuplicated(taxa) || any(!nzchar(taxa)) ||
      !identical(sort(taxa, method="radix"), taxa)) abort_acquisition("FROZEN_106_TAXON_UNIVERSE_DRIFT")
  actual <- digest::digest(paste0(paste(taxa, collapse="\n"), "\n"),
                           algo="sha256", serialize=FALSE)
  if (!identical(actual, FIXED106_SHA256) ||
      !identical(manifest$source_fixed106_sha256, FIXED106_SHA256)) {
    abort_acquisition("FROZEN_106_TAXON_SHA256_MISMATCH")
  }
  expected_countries <- c("BR", "CR", "EC", "GF", "GT", "HN", "NI", "PA", "PE", "SV")
  if (length(manifest$shadow_fitted_countries) != 10L ||
      !setequal(manifest$shadow_fitted_countries, expected_countries)) {
    abort_acquisition("FROZEN_SHADOW_COUNTRY_UNIVERSE_DRIFT")
  }
  taxa
}

main <- function(args=commandArgs(trailingOnly=TRUE)) {
  options(stringsAsFactors=FALSE, warn=1)
  parsed <- parse_arguments(args)
  private_path <- parsed[["private-output"]]
  receipt_path <- parsed[["receipt-output"]]
  if (!requireNamespace("jsonlite", quietly=TRUE)) stop("JSONLITE_REQUIRED", call.=FALSE)
  receipt <- list(
    schema_version=1L, status="BIEN_EXTERNAL_ACQUISITION_IN_PROGRESS",
    started_utc=format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz="UTC"),
    fixed106_taxa_sha256=FIXED106_SHA256,
    query=list(function_name="BIEN_plot_country", country_codes=as.list(names(COUNTRY_NAMES)),
               all_metadata=TRUE, natives_only=TRUE, cultivated=FALSE),
    countries=list(), source_independence_from_original_GBIF="UNKNOWN",
    raw_records_or_coordinates_in_public_receipt=FALSE,
    plot_or_cell_identifiers_in_public_receipt=FALSE,
    bat_outcomes_opened=FALSE, prediction_scores_computed=FALSE
  )
  save_receipt <- function() {
    dir.create(dirname(receipt_path), recursive=TRUE, showWarnings=FALSE)
    jsonlite::write_json(receipt, receipt_path, pretty=TRUE, auto_unbox=TRUE,
                         dataframe="rows", na="null", null="null", digits=NA)
  }
  private_temp <- NULL
  private_written <- FALSE
  failure <- NULL
  tryCatch({
    if (!requireNamespace("BIEN", quietly=TRUE) || !requireNamespace("digest", quietly=TRUE)) {
      abort_acquisition("BIEN_AND_DIGEST_REQUIRED")
    }
    if (identical(normalizePath(private_path, mustWork=FALSE),
                  normalizePath(receipt_path, mustWork=FALSE))) {
      abort_acquisition("PRIVATE_AND_PUBLIC_PATHS_MUST_DIFFER")
    }
    if (file.exists(private_path)) abort_acquisition("PRIVATE_OUTPUT_ALREADY_EXISTS")
    manifest <- jsonlite::fromJSON(parsed$manifest, simplifyVector=TRUE)
    taxa <- validate_manifest(manifest)
    receipt$manifest_sha256 <- digest::digest(file=parsed$manifest, algo="sha256")
    receipt$BIEN_R_package_version <- as.character(utils::packageVersion("BIEN"))
    version <- quiet_query(function() BIEN::BIEN_metadata_database_version(),
                            "BIEN_VERSION_QUERY_FAILED")
    if (!all(c("db_version", "db_release_date") %in% names(version)) || nrow(version) != 1L) {
      abort_acquisition("BIEN_VERSION_SCHEMA_DRIFT")
    }
    receipt$BIEN_database_version <- version[, c("db_version", "db_release_date"), drop=FALSE]
    receipt$stage <- "COUNTRY_PLOT_TABLES"
    save_receipt()
    raw <- list()
    for (code in names(COUNTRY_NAMES)) {
      country <- unname(COUNTRY_NAMES[[code]])
      table <- quiet_query(function() BIEN::BIEN_plot_country(
        country=country, all.metadata=TRUE, natives.only=TRUE, cultivated=FALSE),
        paste0("BIEN_PLOT_QUERY_FAILED_", code))
      if (nrow(table) == 0L) {
        abort_acquisition(paste0("BIEN_PLOT_EMPTY_RESPONSE_", code))
      }
      if (anyDuplicated(names(table)) || !all(REQUIRED_PLOT_COLUMNS %in% names(table))) {
        abort_acquisition(paste0("BIEN_PLOT_SCHEMA_DRIFT_", code))
      }
      # Country labels are returned data; neither infer nor rewrite their value.
      if (anyNA(table$country) || any(as.character(table$country) != country)) {
        abort_acquisition(paste0("BIEN_PLOT_COUNTRY_VALUE_DRIFT_", code))
      }
      raw[[code]] <- table
      receipt$countries[[code]] <- summarize_country(table, taxa, code)
      save_receipt()
    }
    receipt$stage <- "SOURCE_BIBLIOGRAPHY"
    save_receipt()
    sql_query <- getFromNamespace(".BIEN_sql", "BIEN")
    receipt$datasource_bibliography <- fetch_source_bibliography(sql_query)
    dir.create(dirname(private_path), recursive=TRUE, showWarnings=FALSE)
    private_temp <- tempfile(pattern=".bien-private-", tmpdir=dirname(private_path))
    previous_umask <- Sys.umask("0077")
    tryCatch({
      jsonlite::write_json(list(countries=raw), private_temp, pretty=FALSE,
                           auto_unbox=TRUE, dataframe="rows", na="null", null="null", digits=NA,
                           Date="ISO8601", POSIXt="ISO8601")
      Sys.chmod(private_temp, mode="0600")
      if (!file.rename(private_temp, private_path)) abort_acquisition("PRIVATE_OUTPUT_ATOMIC_RENAME_FAILED")
      private_written <- TRUE
    }, finally=Sys.umask(previous_umask))
    receipt$stage <- "COMPLETE"
    receipt$status <- "BIEN_EXTERNAL_ACQUISITION_COMPLETE"
    receipt$completed_utc <- format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz="UTC")
    save_receipt()
  }, error=function(e) {
    # Database diagnostics can contain connection details. Public failure data
    # uses controlled error codes, never arbitrary SQL/driver exception text.
    failure <<- if (inherits(e, "neobat_acquisition_error")) conditionMessage(e) else "UNEXPECTED_BIEN_ACQUISITION_ERROR"
    receipt$status <<- "BIEN_EXTERNAL_ACQUISITION_FAILED"
    receipt$error_code <<- failure
    receipt$error_class <<- class(e)[[1]]
    save_receipt()
  })
  if (!is.null(private_temp) && file.exists(private_temp)) unlink(private_temp)
  if (!is.null(failure)) {
    if (private_written && file.exists(private_path)) unlink(private_path)
    message("BIEN acquisition failed: ", failure)
    return(1L)
  }
  cat("BIEN_EXTERNAL_ACQUISITION_COMPLETE CR=", receipt$countries$CR$total_rows,
      " PA=", receipt$countries$PA$total_rows, "\n", sep="")
  0L
}

if (sys.nframe() == 0L) quit(status=main(), save="no", runLast=FALSE)

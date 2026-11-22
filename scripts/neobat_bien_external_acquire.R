# Official BIEN acquisition within the already-frozen ten-country universe.
# Complete returned rows go only to a private temporary JSON; public output is
# aggregate coverage and explicitly selected datasource bibliography fields.

FIXED106_SHA256 <- "41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6"
COUNTRY_NAMES <- c(BR="Brazil", CR="Costa Rica", EC="Ecuador", GF="French Guiana",
                   GT="Guatemala", HN="Honduras", NI="Nicaragua", PA="Panama",
                   PE="Peru", SV="El Salvador")
DEFAULT_COUNTRIES <- c("CR", "PA")
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
  if (!length(args) %in% c(6L, 8L)) {
    abort_acquisition("USAGE_PRIVATE_OUTPUT_RECEIPT_OUTPUT_MANIFEST_REQUIRED")
  }
  flags <- args[seq.int(1L, length(args), by=2L)]
  values <- args[seq.int(2L, length(args), by=2L)]
  if (anyNA(flags) || anyNA(values) || anyDuplicated(flags) ||
      !all(expected %in% flags) || any(!flags %in% c(expected, "--countries")) ||
      any(!nzchar(values[flags != "--countries"]))) {
    abort_acquisition("USAGE_PRIVATE_OUTPUT_RECEIPT_OUTPUT_MANIFEST_REQUIRED")
  }
  parsed <- setNames(as.list(values), sub("^--", "", flags))
  countries <- DEFAULT_COUNTRIES
  if ("countries" %in% names(parsed)) {
    country_arg <- parsed$countries
    countries <- trimws(strsplit(country_arg, ",", fixed=TRUE)[[1]])
    if (!length(countries) || any(!nzchar(countries)) ||
        grepl(",[[:space:]]*$", country_arg) || anyDuplicated(countries) ||
        any(!countries %in% names(COUNTRY_NAMES))) {
      abort_acquisition("COUNTRY_SELECTION_MUST_BE_UNIQUE_FROZEN_CODES")
    }
  }
  parsed$countries <- countries
  parsed
}

present <- function(x) !is.na(x) & nzchar(trimws(as.character(x)))
numeric_values <- function(x) suppressWarnings(as.numeric(as.character(x)))
distinct_present <- function(x) length(unique(as.character(x)[present(x)]))

clean_species_labels <- function(x) {
  # Match Python's existing " ".join(str(value).split()) behavior for labels.
  # All normalization is derived; the original private table is unchanged.
  whitespace <- "[\\x09-\\x0D\\x1C-\\x1F\\x20\\x{0085}\\x{00A0}\\x{1680}\\x{2000}-\\x{200A}\\x{2028}\\x{2029}\\x{202F}\\x{205F}\\x{3000}]+"
  value <- as.character(x)
  value[is.na(value)] <- ""
  value <- trimws(gsub(whitespace, " ", value, perl=TRUE), whitespace=" ")
  value[tolower(value) %in% c("na", "n/a", "null", "nan")] <- ""
  value
}

validated_datasource_ids <- function(x, allow_missing=FALSE) {
  values <- trimws(as.character(x))
  missing <- !present(values)
  if (any(missing) && !allow_missing) abort_acquisition("BIEN_DATASOURCE_ID_INVALID")
  values <- values[!missing]
  number <- numeric_values(values)
  if (any(!grepl("^[0-9]+$", values)) || any(!is.finite(number)) ||
      any(number < 1 | number > .Machine$integer.max)) {
    abort_acquisition("BIEN_DATASOURCE_ID_INVALID")
  }
  as.integer(number)
}

source_ids_from_tables <- function(tables) {
  values <- unlist(lapply(tables, function(d) as.character(d$datasource_id)), use.names=FALSE)
  sort(unique(validated_datasource_ids(values, allow_missing=TRUE)))
}

validate_country_table <- function(table, code, require_nonempty=FALSE) {
  if (!is.data.frame(table) || anyDuplicated(names(table)) ||
      !all(REQUIRED_PLOT_COLUMNS %in% names(table))) {
    abort_acquisition(paste0("BIEN_PLOT_SCHEMA_DRIFT_", code))
  }
  if (require_nonempty && nrow(table) == 0L) {
    abort_acquisition(paste0("BIEN_PLOT_EMPTY_RESPONSE_", code))
  }
  # An empty complete table passes; NULL/error/missing-schema responses do not.
  # Country labels are returned data, never inferred or rewritten.
  if (anyNA(table$country) || any(as.character(table$country) != unname(COUNTRY_NAMES[[code]]))) {
    abort_acquisition(paste0("BIEN_PLOT_COUNTRY_VALUE_DRIFT_", code))
  }
  invisible(TRUE)
}

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
  species <- clean_species_labels(d$scrubbed_species_binomial)
  hit <- !is.na(species) & species %in% taxa
  focal <- d[hit, , drop=FALSE]
  prior <- list(CR=list(total_rows=21949L, matched_taxa=17L, focal_record_rows=557L),
                PA=list(total_rows=8390L, matched_taxa=22L, focal_record_rows=974L))[[code]]
  list(
    country_code=code, country=unname(COUNTRY_NAMES[[code]]),
    query_completed=TRUE, query_completed_empty=nrow(d) == 0L,
    total_rows=nrow(d), matched_taxa=length(unique(species[hit])),
    focal_record_rows=sum(hit), fixed_taxon_denominator=length(taxa),
    previous_acquisition_counts=prior,
    observed_minus_previous=if (is.null(prior)) NULL else
      list(total_rows=nrow(d)-prior$total_rows,
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

source_metadata_query <- function(columns, datasource_ids=FIXED_SOURCE_IDS) {
  if (!length(columns) || any(!columns %in% SAFE_SOURCE_COLUMNS)) {
    abort_acquisition("UNSAFE_DATASOURCE_COLUMN_SELECTION")
  }
  selected <- paste(sprintf('"%s"', columns), collapse=", ")
  ids <- sort(unique(validated_datasource_ids(datasource_ids)))
  if (!length(ids)) {
    return(paste0("SELECT ", selected, " FROM datasource WHERE FALSE ORDER BY datasource_id;"))
  }
  requested <- paste(ids, collapse=", ")
  paste0("SELECT ", selected, " FROM datasource WHERE datasource_id IN (", requested,
         ") OR datasource_id IN (SELECT proximate_provider_datasource_id FROM datasource ",
         "WHERE datasource_id IN (", requested, ")) ORDER BY datasource_id;")
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

fetch_source_bibliography <- function(sql_query, datasource_ids=FIXED_SOURCE_IDS, fixed_scope=TRUE) {
  requested_ids <- sort(unique(validated_datasource_ids(datasource_ids)))
  if (fixed_scope && !identical(requested_ids, FIXED_SOURCE_IDS)) {
    abort_acquisition("BIEN_FIXED_DATASOURCE_UNIVERSE_DRIFT")
  }
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
  sources <- quiet_query(function() sql_query(source_metadata_query(selected, requested_ids)),
                         "BIEN_DATASOURCE_BIBLIOGRAPHY_QUERY_FAILED")
  if (!identical(names(sources), selected)) abort_acquisition("BIEN_DATASOURCE_RETURNED_SCHEMA_DRIFT")
  ids <- as.character(validated_datasource_ids(sources$datasource_id))
  requested <- as.character(requested_ids)
  if (anyDuplicated(ids) || !all(requested %in% ids)) {
    abort_acquisition(if (fixed_scope) "BIEN_FIXED_DATASOURCE_UNIVERSE_DRIFT" else
                       "BIEN_REQUESTED_DATASOURCE_UNIVERSE_DRIFT")
  }
  original <- sources[ids %in% requested, , drop=FALSE]
  proximate <- unique(as.character(validated_datasource_ids(
    original$proximate_provider_datasource_id, allow_missing=TRUE)))
  if (!all(proximate %in% ids)) abort_acquisition("BIEN_PROXIMATE_PROVIDER_ROW_MISSING")
  if (!setequal(ids, union(requested, proximate))) {
    abort_acquisition("BIEN_DATASOURCE_QUERY_UNIVERSE_DRIFT")
  }
  # Values from bibliography columns only. Do not pass through SELECT * data.
  for (column in selected) {
    sources[[column]] <- clean_public_source_text(sources[[column]])
  }
  list(
    fixed_datasource_ids=if (fixed_scope) as.list(FIXED_SOURCE_IDS) else NULL,
    queried_datasource_ids=as.list(requested_ids),
    datasource_id_scope=if (fixed_scope) "HISTORICAL_CR_PA_FIXED_SIX" else "ALL_RETURNED_COUNTRY_ROWS",
    proximate_provider_datasource_ids=as.list(sort(proximate)),
    available_column_names=available,
    selected_public_column_names=selected,
    source_rows=sources,
    fixed_sources_with_nonempty_citation=if (fixed_scope) sum(present(original$source_citation)) else NULL,
    queried_sources_with_nonempty_citation=sum(present(original$source_citation)),
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
  countries <- parsed$countries
  default_scope <- length(countries) == 2L && setequal(countries, DEFAULT_COUNTRIES)
  private_path <- parsed[["private-output"]]
  receipt_path <- parsed[["receipt-output"]]
  if (!requireNamespace("jsonlite", quietly=TRUE)) stop("JSONLITE_REQUIRED", call.=FALSE)
  receipt <- list(
    schema_version=1L, status="BIEN_EXTERNAL_ACQUISITION_IN_PROGRESS",
    started_utc=format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz="UTC"),
    fixed106_taxa_sha256=FIXED106_SHA256,
    query=list(function_name="BIEN_plot_country", country_codes=as.list(countries),
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
    for (code in countries) {
      country <- unname(COUNTRY_NAMES[[code]])
      table <- quiet_query(function() BIEN::BIEN_plot_country(
        country=country, all.metadata=TRUE, natives.only=TRUE, cultivated=FALSE),
        paste0("BIEN_PLOT_QUERY_FAILED_", code))
      validate_country_table(table, code, require_nonempty=default_scope)
      raw[[code]] <- table
      receipt$countries[[code]] <- summarize_country(table, taxa, code)
      save_receipt()
    }
    receipt$stage <- "SOURCE_BIBLIOGRAPHY"
    save_receipt()
    sql_query <- getFromNamespace(".BIEN_sql", "BIEN")
    source_ids <- if (default_scope) FIXED_SOURCE_IDS else source_ids_from_tables(raw)
    receipt$datasource_bibliography <- fetch_source_bibliography(
      sql_query, datasource_ids=source_ids, fixed_scope=default_scope)
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
  country_counts <- vapply(countries, function(code) {
    paste0(code, "=", receipt$countries[[code]]$total_rows)
  }, character(1))
  cat("BIEN_EXTERNAL_ACQUISITION_COMPLETE ", paste(country_counts, collapse=" "), "\n", sep="")
  0L
}

if (sys.nframe() == 0L) quit(status=main(), save="no", runLast=FALSE)

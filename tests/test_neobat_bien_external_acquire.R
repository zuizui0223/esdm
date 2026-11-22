# Acquisition boundary tests only; no database access or model evaluation.
source("scripts/neobat_bien_external_acquire.R")
stopifnot(requireNamespace("jsonlite", quietly=TRUE))

expect_acquisition_error <- function(expr, code) {
  error <- tryCatch({ force(expr); NULL }, error=function(e) e)
  stopifnot(inherits(error, "neobat_acquisition_error"),
            identical(conditionMessage(error), code))
}

# Missing optional country selection retains the established CR/PA scope.
base_args <- c("--private-output", "private.json", "--receipt-output", "receipt.json",
               "--manifest", "manifest.json")
stopifnot(identical(parse_arguments(base_args)$countries, c("CR", "PA")))
stopifnot(identical(parse_arguments(c(base_args, "--countries", "BR,GF"))$countries,
                    c("BR", "GF")))
for (invalid in c("", "US", "br", "BR,BR", "BR,", ",BR", "BR,,GF")) {
  expect_acquisition_error(parse_arguments(c(base_args, "--countries", invalid)),
                           "COUNTRY_SELECTION_MUST_BE_UNIQUE_FROZEN_CODES")
}
expect_acquisition_error(parse_arguments(c(base_args, "--countries", "BR",
                                           "--countries", "EC")),
                         "USAGE_PRIVATE_OUTPUT_RECEIPT_OUTPUT_MANIFEST_REQUIRED")

available <- c("datasource_id", "source_name", "source_fullname",
               "proximate_provider_datasource_id", "source_citation",
               "source_url", "license", "primary_contact_email",
               "primary_contact_fullname", "password")
selected <- source_metadata_columns(available)
stopifnot(!any(c("primary_contact_email", "primary_contact_fullname", "password") %in% selected))
query <- source_metadata_query(selected)
stopifnot(!grepl("SELECT \\*", query), !grepl("primary_contact|password", query))
stopifnot(grepl("proximate_provider_datasource_id", query, fixed=TRUE))
stopifnot(grepl("IN (18, 27, 37, 40, 59, 66)", query, fixed=TRUE))
new_query <- source_metadata_query(selected, c(71L, 72L))
stopifnot(grepl("IN (71, 72)", new_query, fixed=TRUE),
          !grepl("IN (18,", new_query, fixed=TRUE),
          grepl("WHERE FALSE", source_metadata_query(selected, integer()), fixed=TRUE))
for (invalid_id in c("18); SELECT * FROM datasource; --", "1.5", "-1", "Inf", "1e3",
                    "0", "2147483648", NA_character_)) {
  expect_acquisition_error(source_metadata_query(selected, invalid_id),
                           "BIEN_DATASOURCE_ID_INVALID")
}

# Public aggregate output must not echo plot labels, coordinates, observer names,
# or raw methodology strings, even when the private input contains them.
d <- as.data.frame(setNames(rep(list(c(NA_character_, NA_character_)),
                               length(REQUIRED_PLOT_COLUMNS)), REQUIRED_PLOT_COLUMNS))
d$country <- c("Costa Rica", "Costa Rica")
d$plot_name <- c("PRIVATE_PLOT_123", "PRIVATE_PLOT_456")
d$scrubbed_species_binomial <- c("Cecropia obtusifolia", "A different taxon")
d$datasource_id <- c("27", "27")
d$datasource <- c("SALVIAS", "SALVIAS")
d$dataset <- c("PRIVATE_DATASET_LABEL", "PRIVATE_DATASET_LABEL")
d$sampling_protocol <- c("PRIVATE_METHOD", NA_character_)
d$recorded_by <- c("PRIVATE_CONTACT", "PRIVATE_CONTACT")
d$latitude <- c(8.1234567, 9.1234567)
d$longitude <- c(-83.1234567, -84.1234567)
d$coord_uncertainty_m <- c(50, NA_real_)
d$date_collected <- as.Date(c("2001-01-01", NA))
d$plot_area_ha <- c(1, 1)
summary <- summarize_country(d, c("Cecropia obtusifolia", "Ficus insipida"), "CR")
stopifnot(summary$total_rows == 2L,
          summary$matched_taxa == 1L,
          summary$focal_record_rows == 1L,
          summary$coverage_all$rows_with_date_collected == 1L,
          summary$coverage_all$rows_with_sampling_protocol == 1L,
          summary$coverage_all$rows_with_finite_nonnegative_uncertainty == 1L)
encoded <- jsonlite::toJSON(summary, auto_unbox=TRUE, null="null", na="null")
for (private_value in c("PRIVATE_PLOT", "PRIVATE_METHOD", "PRIVATE_CONTACT",
                        "PRIVATE_DATASET_LABEL", "83.1234567", "8.1234567")) {
  stopifnot(!grepl(private_value, encoded, fixed=TRUE))
}
stopifnot(identical(clean_public_source_text("Reach author@example.org"),
                    "Reach [REDACTED_EMAIL]"))
stopifnot(!grepl("secret", clean_public_source_text("https://user:secret@example.org/data"), fixed=TRUE))

# A new country's receipt has no invented historical comparison. Matching uses
# the scorer's whitespace normalization, but private rows retain original text.
new_country <- d
new_country$country <- c("Brazil", "Brazil")
new_country$datasource_id <- c("71", "72")
new_country$scrubbed_species_binomial[[1]] <- "  Cecropia\t\u00a0obtusifolia\n"
stopifnot(identical(clean_species_labels(c("  Cecropia\t\u00a0obtusifolia\n", "NA", NA_character_,
                                          "Ficus\u2003insipida", "\u001cFicus insipida\u001f")),
                    c("Cecropia obtusifolia", "", "", "Ficus insipida", "Ficus insipida")))
new_summary <- summarize_country(new_country, c("Cecropia obtusifolia", "Ficus insipida"), "BR")
stopifnot(new_summary$matched_taxa == 1L, new_summary$focal_record_rows == 1L,
          new_summary$focal_record_counts[["Cecropia obtusifolia"]] == 1L,
          is.null(new_summary$previous_acquisition_counts),
          is.null(new_summary$observed_minus_previous),
          isTRUE(new_summary$query_completed), !new_summary$query_completed_empty,
          identical(new_country$scrubbed_species_binomial[[1]], "  Cecropia\t\u00a0obtusifolia\n"))

# A successfully returned zero-row table is distinct from a failed query or a
# missing schema. It remains an explicit empty array in private serialization.
empty <- d[FALSE, , drop=FALSE]
validate_country_table(empty, "GF", require_nonempty=FALSE)
empty_summary <- summarize_country(empty, c("Cecropia obtusifolia", "Ficus insipida"), "GF")
stopifnot(isTRUE(empty_summary$query_completed), isTRUE(empty_summary$query_completed_empty),
          empty_summary$total_rows == 0L, empty_summary$matched_taxa == 0L,
          empty_summary$focal_record_rows == 0L,
          empty_summary$fixed_taxon_denominator == 2L,
          identical(empty_summary$focal_record_counts,
                    list("Cecropia obtusifolia"=0L, "Ficus insipida"=0L)),
          isTRUE(empty_summary$unobserved_taxa_are_not_absent))
expect_acquisition_error(validate_country_table(empty, "CR", require_nonempty=TRUE),
                         "BIEN_PLOT_EMPTY_RESPONSE_CR")
expect_acquisition_error(validate_country_table(empty[, -1, drop=FALSE], "GF", require_nonempty=FALSE),
                         "BIEN_PLOT_SCHEMA_DRIFT_GF")
expect_acquisition_error(validate_country_table(d, "BR", require_nonempty=FALSE),
                         "BIEN_PLOT_COUNTRY_VALUE_DRIFT_BR")
expect_acquisition_error(quiet_query(function() stop("PRIVATE_DATABASE_ERROR"), "CONTROLLED_QUERY_FAILURE"),
                         "CONTROLLED_QUERY_FAILURE")

# The bibliography must include nonfocal source IDs from full returned tables,
# validate IDs before interpolating SQL, and request only immediate providers.
stopifnot(identical(source_ids_from_tables(list(BR=new_country, GF=empty)), c(71L, 72L)),
          identical(source_ids_from_tables(list(GF=empty)), integer()))
missing_id_country <- new_country
missing_id_country$datasource_id[[2]] <- NA_character_
stopifnot(identical(source_ids_from_tables(list(BR=missing_id_country)), 71L))
bad_id_country <- new_country
bad_id_country$datasource_id[[2]] <- "72 OR TRUE"
expect_acquisition_error(source_ids_from_tables(list(BR=bad_id_country)), "BIEN_DATASOURCE_ID_INVALID")

bibliography_rows <- data.frame(
  datasource_id=c(71L, 72L, 900L), source_name=c("source71", "source72", "provider"),
  source_fullname=c("Study 71", "Study 72", "Provider"),
  proximate_provider_datasource_id=c(900L, 900L, 901L),
  source_citation=c("Study citation", NA_character_, "Contact author@example.org"),
  source_url=c("https://example.org/71", NA_character_, "https://example.org/network"),
  license=c("acknowledge", "acknowledge", "acknowledge"), check.names=FALSE)
fake_metadata_query <- function(rows) {
  force(rows)
  function(sql) {
    if (grepl("pg_catalog.pg_attribute", sql, fixed=TRUE)) {
      return(data.frame(column_name=available))
    }
    stopifnot(grepl("IN (71, 72)", sql, fixed=TRUE) || grepl("WHERE FALSE", sql, fixed=TRUE),
              !grepl("SELECT \\*|primary_contact|password", sql))
    rows
  }
}
bibliography <- fetch_source_bibliography(fake_metadata_query(bibliography_rows),
                                        datasource_ids=c(71L, 72L), fixed_scope=FALSE)
stopifnot(identical(bibliography$queried_datasource_ids, list(71L, 72L)),
          is.null(bibliography$fixed_datasource_ids),
          identical(bibliography$proximate_provider_datasource_ids, list("900")),
          bibliography$queried_sources_with_nonempty_citation == 1L,
          bibliography$source_rows$source_citation[[3]] == "Contact [REDACTED_EMAIL]",
          !bibliography$contact_or_credential_columns_queried,
          nrow(bibliography$source_rows) == 3L)
expect_acquisition_error(fetch_source_bibliography(
  fake_metadata_query(bibliography_rows[1:2, , drop=FALSE]), c(71L, 72L), fixed_scope=FALSE),
  "BIEN_PROXIMATE_PROVIDER_ROW_MISSING")
extra_provider <- bibliography_rows[3, , drop=FALSE]
extra_provider$datasource_id <- 901L
expect_acquisition_error(fetch_source_bibliography(
  fake_metadata_query(rbind(bibliography_rows, extra_provider)), c(71L, 72L), fixed_scope=FALSE),
  "BIEN_DATASOURCE_QUERY_UNIVERSE_DRIFT")
empty_bibliography <- fetch_source_bibliography(
  fake_metadata_query(bibliography_rows[FALSE, , drop=FALSE]), integer(), fixed_scope=FALSE)
stopifnot(length(empty_bibliography$queried_datasource_ids) == 0L,
          nrow(empty_bibliography$source_rows) == 0L,
          empty_bibliography$queried_sources_with_nonempty_citation == 0L)

# jsonlite must preserve row arrays, complete fields and null values privately.
private <- list(countries=list(CR=d, PA=d[1, , drop=FALSE], GF=empty))
roundtrip <- jsonlite::fromJSON(jsonlite::toJSON(private, dataframe="rows",
                          auto_unbox=TRUE, na="null", null="null", digits=NA),
                          simplifyVector=FALSE)
stopifnot(length(roundtrip$countries$CR) == 2L,
          length(roundtrip$countries$PA) == 1L,
          length(roundtrip$countries$GF) == 0L,
          roundtrip$countries$PA[[1]]$plot_name == "PRIVATE_PLOT_123",
          is.null(roundtrip$countries$CR[[2]]$date_collected))
cat("PASS: acquisition scope, explicit empty queries, privacy, numeric source bibliography, coverage, and private JSON schema\n")

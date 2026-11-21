# Acquisition boundary tests only; no database access or model evaluation.
source("scripts/neobat_bien_external_acquire.R")
stopifnot(requireNamespace("jsonlite", quietly=TRUE))

available <- c("datasource_id", "source_name", "source_fullname",
               "proximate_provider_datasource_id", "source_citation",
               "source_url", "license", "primary_contact_email",
               "primary_contact_fullname", "password")
selected <- source_metadata_columns(available)
stopifnot(!any(c("primary_contact_email", "primary_contact_fullname", "password") %in% selected))
query <- source_metadata_query(selected)
stopifnot(!grepl("SELECT \\*", query), !grepl("primary_contact|password", query))
stopifnot(grepl("proximate_provider_datasource_id", query, fixed=TRUE))

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

# jsonlite must preserve row arrays, complete fields and null values privately.
private <- list(countries=list(CR=d, PA=d[1, , drop=FALSE]))
roundtrip <- jsonlite::fromJSON(jsonlite::toJSON(private, dataframe="rows",
                          auto_unbox=TRUE, na="null", null="null", digits=NA),
                          simplifyVector=FALSE)
stopifnot(length(roundtrip$countries$CR) == 2L,
          length(roundtrip$countries$PA) == 1L,
          roundtrip$countries$PA[[1]]$plot_name == "PRIVATE_PLOT_123",
          is.null(roundtrip$countries$CR[[2]]$date_collected))
cat("PASS: acquisition privacy, bibliography whitelist, coverage, and private JSON schema\n")

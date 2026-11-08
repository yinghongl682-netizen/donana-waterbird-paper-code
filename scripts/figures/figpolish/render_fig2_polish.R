# Reflow the verified selected Fig. 2 ggplot object without rebuilding study data.
# Run: Rscript --vanilla render_fig2_polish.R <P1 f23 output root> <R library> <output directory>
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 3L, dir.exists(args[[1L]]), dir.exists(args[[2L]]))
input_root <- normalizePath(args[[1L]], winslash = "/", mustWork = TRUE)
library_root <- normalizePath(args[[2L]], winslash = "/", mustWork = TRUE)
dir.create(args[[3L]], recursive = TRUE, showWarnings = FALSE)
out <- normalizePath(args[[3L]], winslash = "/", mustWork = TRUE)
stopifnot(out != input_root, !startsWith(tolower(out), paste0(tolower(input_root), "/")))
.libPaths(c(library_root, .Library), include.site = FALSE)
locale <- Sys.setlocale("LC_CTYPE", "English_United States.utf8")
stopifnot(nzchar(locale))
options(device = function(...) stop("Unexpected default graphics device"))
suppressPackageStartupMessages(library(ggplot2))
# The selected RDS stores an incomplete theme, so bind its original device theme.
theme_set(theme_classic(base_size = 9, base_family = "Arial") + theme(
  axis.line = element_line(linewidth = .3, colour = "#353535"),
  axis.ticks = element_line(linewidth = .25), axis.text = element_text(colour = "#202020", size = 8),
  axis.title = element_text(size = 9), strip.background = element_rect(fill = "#F0F2F3", colour = NA),
  strip.text = element_text(size = 9, face = "italic"), legend.position = "bottom",
  legend.text = element_text(size = 9), legend.title = element_text(size = 9),
  plot.margin = margin(3, 3, 3, 3)
))

stem <- file.path(out, "FIG2_POLISH")
source_dir <- file.path(input_root, "formal", "03_repaired_figure_sources", "F2")
inputs <- c(
  selected_rds = file.path(input_root, "03_F2", "Fig2_FIGV1_SELECTED_SYSTEM_CANDIDATE_PLOT.rds"),
  selected_svg = file.path(input_root, "03_F2", "Fig2_FIGV1_SELECTED_SYSTEM_CANDIDATE.svg"),
  display = file.path(source_dir, "FIG2_EXACT_DISPLAY_DATA.csv"),
  peaks = file.path(source_dir, "FIG2_SOURCE_DEFINED_PEAK_MARKS.csv"),
  december = file.path(source_dir, "F2_DISPLACED_ANNOTATION_SOURCE_LINK.csv")
)
sha <- function(path) digest::digest(readBin(path, "raw", n = file.info(path)$size), algo = "sha256", serialize = FALSE)
input_sha <- vapply(inputs, sha, character(1))
stopifnot(input_sha[["selected_rds"]] == "08924cd948d8deb91856f8a3d0325544e82b9dce040be42122051ca77ac62dfe",
          input_sha[["selected_svg"]] == "6381e760be2521cf755b667278989c88aa5dc1f63d6d1d0a5bb66a837076f882")

# Keep the actual frozen objects, mappings, scales, and local Dec annotation anchor.
original <- readRDS(inputs[["selected_rds"]])
candidate <- readRDS(inputs[["selected_rds"]])
stopifnot(length(candidate$layers) == 6L, inherits(candidate$layers[[6L]]$geom, "GeomText"))
candidate$layers[[6L]]$aes_params$size <- 9 / ggplot2::.pt
candidate <- candidate + theme(
  text = element_text(family = "Arial", colour = "#252A2E"),
  axis.text.x = element_text(angle = 66, hjust = 1, vjust = 1, size = 9,
                             margin = margin(t = 3)),
  axis.text.y = element_text(size = 9, margin = margin(r = 2)),
  axis.title.y = element_text(size = 9.5, margin = margin(r = 5)),
  strip.text = element_text(face = "italic", size = 10, margin = margin(3, 3, 3, 3)),
  legend.text = element_text(size = 9.5),
  legend.key.width = grid::unit(6.5, "mm"),
  legend.spacing.x = grid::unit(2, "mm"),
  legend.box.spacing = grid::unit(1.5, "mm"),
  panel.spacing.x = grid::unit(3.1, "mm"),
  panel.spacing.y = grid::unit(3.8, "mm"),
  plot.margin = margin(5, 5, 5, 5)
)

before <- ggplot_build(original)
after <- ggplot_build(candidate)
data <- original$data
key <- function(rows) paste(rows$species, rows$parent_id, rows$month, sep = "|")
display <- read.csv(inputs[["display"]], na.strings = c("NA", ""))
index <- match(key(data), key(display))
stopifnot(!anyNA(index), !anyDuplicated(key(display)), length(index) == nrow(display))
display <- display[index, , drop = FALSE]
peak_csv <- read.csv(inputs[["peaks"]])
dec_csv <- read.csv(inputs[["december"]])
callout <- candidate$layers[[5L]]$data
fields <- c("month", "n_years", "n_events", "median_log1p")
csv_matches <- vapply(fields, function(field) {
  all(is.na(data[[field]]) == is.na(display[[field]])) &&
    all(abs(data[[field]] - display[[field]]) < 1e-13, na.rm = TRUE)
}, logical(1))
peak_keys <- c(key(candidate$layers[[3L]]$data), key(callout))
axis_keys <- function(build) {
  lapply(build$layout$panel_params, function(panel) {
    list(x_range = as.numeric(panel$x.range), y_range = as.numeric(panel$y.range),
         x_breaks = as.numeric(panel$x$breaks), y_breaks = as.numeric(panel$y$breaks))
  })
}
label_columns <- setdiff(names(before$data[[6L]]), "size")
support_by_species <- aggregate(n_events ~ species + parent_id, data, sum)
coverage <- c(PNC = 75L, SB = 113L)
same_support <- all(support_by_species$n_events == coverage[support_by_species$parent_id])
check <- c(
  plot_data = identical(data, candidate$data),
  published_display_fields = all(csv_matches) && identical(data$reference_state, display$reference_state),
  nine_panel_species_order = nrow(before$layout$layout) == 9L &&
    identical(before$layout$layout, after$layout$layout),
  original_axes_and_units = identical(axis_keys(before), axis_keys(after)) &&
    identical(original$labels$x, candidate$labels$x) && identical(original$labels$y, candidate$labels$y),
  all_august_na = sum(is.na(data$median_log1p)) == 18L &&
    all(is.na(data$median_log1p[data$month == 8L])),
  event_support_pnc_75_sb_113 = same_support && nrow(support_by_species) == 18L,
  frozen_peaks_17_direct_1_displaced = length(peak_keys) == 18L &&
    identical(sort(peak_keys), sort(key(peak_csv))),
  dec_source_identity = nrow(callout) == 1L && identical(key(callout), key(dec_csv)) &&
    callout$source_month == 12L && callout$parent_id == "PNC" &&
    as.character(callout$species) == "Recurvirostra avosetta" &&
    abs(callout$source_median_log1p - dec_csv$source_median_log1p) < 1e-13,
  dec_label_anchor = identical(before$data[[6L]][label_columns], after$data[[6L]][label_columns]),
  vapply(seq_len(5), function(i) identical(before$data[[i]], after$data[[i]]), logical(1))
)
names(check)[(length(check)-4L):length(check)] <- c(
  "sector_lines_data_and_encoding", "sector_points_data_and_encoding",
  "peak_rings_data_and_encoding", "dec_leader_coordinates", "dec_offset_ring_coordinates"
)
if (!all(check)) { print(check); stop('Scientific lock failed') }

w_mm <- 174
h_mm <- 185
for (device in c("svg", "pdf", "_WORD.svg", "_600dpi.png")) {
  suffix <- if (device %in% c("svg", "pdf")) paste0(".", device) else device
  path <- paste0(stem, suffix)
  stopifnot(!file.exists(path))
  if (device == "svg") {
    svglite::svglite(path, width = w_mm / 25.4, height = h_mm / 25.4, bg = "white")
  } else if (device == "pdf") {
    grDevices::cairo_pdf(path, width = w_mm / 25.4, height = h_mm / 25.4,
                         family = "Arial", bg = "white")
  } else if (device == "_WORD.svg") {
    grDevices::svg(path, width = w_mm / 25.4, height = h_mm / 25.4,
                   family = "Arial", bg = "white", onefile = FALSE)
  } else {
    ragg::agg_png(path, width = w_mm, height = h_mm, units = "mm",
                  res = 600, background = "white")
  }
  print(candidate)
  invisible(grDevices::dev.off())
}
for (dpi in c(96, 150, 300)) {
  proof <- pdftools::pdf_render_page(paste0(stem, ".pdf"), page = 1L, dpi = dpi)
  png::writePNG(proof, paste0(stem, "_PDF_", dpi, "dpi.png"), dpi = dpi)
}
saveRDS(candidate, paste0(stem, "_PLOT.rds"))
font_report <- pdftools::pdf_fonts(paste0(stem, ".pdf"))
stopifnot(nrow(font_report) == 2L, all(font_report$embedded),
          all(grepl("Arial", font_report$name, fixed = TRUE)))
svg_text <- xml2::xml_find_all(xml2::read_xml(paste0(stem, ".svg")), './/*[local-name()="text"]')
svg_labels <- xml2::xml_text(svg_text)
baseline_text <- xml2::xml_find_all(xml2::read_xml(inputs[["selected_svg"]]), './/*[local-name()="text"]')
stopifnot(identical(xml2::xml_text(baseline_text), svg_labels),
          sum(svg_labels == "Dec") == 4L, !any(grepl("^-\\d", svg_labels, perl = TRUE)))
font_sizes <- as.numeric(sub(".*font-size: ([0-9.]+)px.*", "\\1", xml2::xml_attr(svg_text, "style")))
stopifnot(!anyNA(font_sizes), min(font_sizes) >= 9)

pdf_bounds <- pdftools::pdf_data(paste0(stem, ".pdf"))[[1L]]
page_dims <- pdftools::pdf_pagesize(paste0(stem, ".pdf"))
stopifnot(all(pdf_bounds$x >= 0), all(pdf_bounds$y >= 0),
          all(pdf_bounds$x + pdf_bounds$width <= page_dims$width),
          all(pdf_bounds$y + pdf_bounds$height <= page_dims$height))
write.csv(pdf_bounds, file.path(out, "F2_PDF_TEXT_BOUNDS.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(data.frame(figure = "Fig. 2", object = names(check), exact_equal = unname(check),
                     baseline = "Verified selected P1 plot and display/peak/December inputs",
                     candidate = "Typography-only rerender", stringsAsFactors = FALSE),
          file.path(out, "F2_SCIENTIFIC_LOCK.csv"), row.names = FALSE, fileEncoding = "UTF-8")
stopifnot(identical(input_sha, vapply(inputs, sha, character(1))))
jsonlite::write_json(list(
  state = "SCIENTIFIC_LOCK_AND_ARTWORK_EXPORT_PASS_AUTHOR_REVIEW_REQUIRED",
  input_sha256 = as.list(input_sha), layer_checks = as.list(check),
  display_rows = nrow(data), non_reportable = sum(is.na(data$median_log1p)),
  species = levels(data$species), event_support = as.list(coverage),
  peak_marks = 18L, svg_text_nodes = length(svg_labels), min_font_pt = min(font_sizes),
  physical_mm = c(width = w_mm, height = h_mm), pdf_fonts = font_report,
  reference_grid = "April 2013 to June 2023",
  cairo_svg_role = "Optional Word artwork with outlines. Keep editable SVG and font-embedded PDF."
), file.path(out, "F2_SOURCE_AND_QA.json"), pretty = TRUE, auto_unbox = TRUE)
cat("F2_ALL_SOURCE_LOCKS_PASS\n")

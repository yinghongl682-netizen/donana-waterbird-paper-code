# Re-render only the two inherited S4 pages with congested colorbar ticks from its unmodified plotting statements.
# Usage: Rscript --vanilla render_s4_legend_spacing.R PARENT_MONTH_CSV FROZEN_ORIGINAL_PNG NEW_OUTPUT_DIR R_LIBRARY
args <- commandArgs(trailingOnly=TRUE)
if(length(args)!=4L)stop('Expected frozen parent-month CSV, original PNG, new output and R package library')
input <- normalizePath(args[1],winslash='/',mustWork=TRUE)
original_png <- normalizePath(args[2],winslash='/',mustWork=TRUE)
if(file.exists(args[3]))stop('Output directory already exists')
dir.create(args[3],recursive=TRUE)
output <- normalizePath(args[3],winslash='/',mustWork=TRUE)
.libPaths(c(normalizePath(args[4],winslash='/'),.Library),include.site=FALSE)
stopifnot(nzchar(Sys.setlocale('LC_CTYPE','English_United States.utf8')))
options(warn=1,device=function(...)stop('UNPLANNED_DEFAULT_GRAPHICS_DEVICE_BLOCKED'))
suppressPackageStartupMessages({library(ggplot2);library(grid);library(jsonlite);library(digest);library(pdftools);library(png);library(xml2)})
script <- sub('^--file=','',grep('^--file=',commandArgs(FALSE),value=TRUE))
original_source <- file.path(dirname(normalizePath(script,winslash='/')),'render_bridge_figures_p1_original.R')
hash<-function(p)digest(readBin(p,'raw',n=file.info(p)$size),algo='sha256',serialize=FALSE)
stopifnot(hash(input)=='8f41b544a299ebfa361732ff285762d7e87d407f8a4615d0ea6fd45f32515f26',
          hash(original_source)=='a8d847ec84370d9fe38b338c85dba7397255a047c7dadee376fdfb45d7535ea8')
binding <- data.frame(
  sha256=c('377160eed67a88bb8f82d167cc263c348270c07a5841a03dd484d19a48a257a9',
           'ea26e9f4adfd9de36f329e2a472f11eb87912724beb1f6640ee5c3bf8efec468'),
  species=c('Ciconia ciconia','Tadorna tadorna'),figure=c('S4_04','S4_13'),ticks=c(7L,5L))
selected <- binding[binding$sha256==hash(original_png),]
stopifnot(nrow(selected)==1L)
asset <- function(suffix) paste0(selected$figure,suffix)
src <- readLines(original_source,encoding='UTF-8',warn=FALSE)
one <- function(pattern){at<-grep(pattern,src);stopifnot(length(at)==1L);at}
styles <- src[one('^blue<-'):one('^safe<-')-1L]
drawing <- src[one('^pm<-read'):one('^# S5 temporal')-1L]
local_scope <- new.env(parent=environment())
local_scope$read <- function(rel) {
  stopifnot(identical(rel,'results/ground/PARENT_MONTH_CONTRIBUTIONS.csv'))
  read.csv(input,stringsAsFactors=FALSE,check.names=FALSE,fileEncoding='UTF-8-BOM')
}
local_scope$annual <- data.frame(species=selected$species)
local_scope$export <- function(p,id,w=174,h=180) {
  stopifnot(identical(id,'S4_01'),w==174,h==210)
  p
}
eval(parse(text=styles),envir=local_scope)
eval(parse(text=drawing),envir=local_scope)
old <- local_scope$p
before <- ggplot_build(old)
stopifnot(nrow(before$data[[1]])==300L,nrow(before$data[[2]])==300L)
save <- function(p,device,name,...) {
  device(file.path(output,name),...)
  on.exit(dev.off())
  print(p)
}
save(old,ragg::agg_png,asset('_ORIGINAL_REPLAY_300dpi.png'),width=174,height=210,units='mm',res=300,background='white')
replay <- file.path(output,asset('_ORIGINAL_REPLAY_300dpi.png'))
stopifnot(hash(replay)==hash(original_png))
# Legend guide geometry only. The limit, break generator, palette, tile text and layer mappings remain in the original plot.
revised <- old+guides(fill=guide_colourbar(theme=theme(
  legend.key.width=unit(65,'mm'),legend.key.height=unit(3.3,'mm'),
  legend.title.position='top',legend.title=element_text(size=9,hjust=.5),
  legend.text=element_text(size=9))))
after <- ggplot_build(revised)
stopifnot(identical(before$data,after$data))
fill_before <- before$plot$scales$get_scales('fill')
fill_after <- after$plot$scales$get_scales('fill')
ticks <- fill_before$get_breaks()
labels <- fill_before$get_labels(ticks)
visible <- is.finite(ticks) & ticks >= min(fill_before$get_limits()) & ticks <= max(fill_before$get_limits())
stopifnot(identical(ticks,fill_after$get_breaks()),identical(labels,fill_after$get_labels(ticks)),
          identical(fill_before$get_limits(),fill_after$get_limits()),
          identical(fill_before$map(ticks),fill_after$map(ticks)),
          sum(visible)==selected$ticks)
save(revised,svglite::svglite,asset('_LEGEND_REPAIR.svg'),width=174/25.4,height=210/25.4,bg='white')
save(revised,grDevices::svg,asset('_LEGEND_REPAIR_WORD.svg'),width=174/25.4,height=210/25.4,onefile=TRUE,family='Arial')
save(revised,grDevices::cairo_pdf,asset('_LEGEND_REPAIR.pdf'),width=174/25.4,height=210/25.4,family='Arial')
save(revised,ragg::agg_png,asset('_LEGEND_REPAIR_600dpi.png'),width=174,height=210,units='mm',res=600,background='white')
candidate_pdf <- file.path(output,asset('_LEGEND_REPAIR.pdf'))
for(dpi in c(96,150)) {
  writePNG(pdf_render_page(candidate_pdf,dpi=dpi),file.path(output,asset(paste0('_LEGEND_REPAIR_PROOF_',dpi,'dpi.png'))),dpi=dpi)
}
tx <- pdf_data(candidate_pdf,font_info=TRUE)[[1]]
tick_rows <- tx[tx$y>max(tx$y)-4 & tx$text%in%labels[visible],]
tick_rows <- tick_rows[order(tick_rows$x),]
stopifnot(identical(tick_rows$text,labels[visible]))
gaps <- tick_rows$x[-1] - (tick_rows$x+tick_rows$width)[-nrow(tick_rows)]
stopifnot(all(gaps>5),all(pdf_fonts(candidate_pdf)$embedded))
write.csv(tick_rows,file.path(output,asset('_COLORBAR_PDF_TEXT_BOUNDS.csv')),row.names=FALSE,fileEncoding='UTF-8')
result <- list(source_sha256=hash(original_source),input_sha256=hash(input),native_baseline_sha256=hash(original_png),
               exact_baseline_png_replay=hash(replay)==hash(original_png),
               tile_and_text_layers_exact=identical(before$data,after$data),tile_count=nrow(before$data[[1]]),
               labelled_value_count=nrow(before$data[[2]]),support_order_exact=identical(before$layout$layout,after$layout$layout),
               exact_fill_limits=fill_after$get_limits(),exact_breaks=ticks[visible],exact_labels=labels[visible],
               tick_pdf_gaps_pt=gaps,tick_min_gap_pt=min(gaps),pdf_fonts_embedded=all(pdf_fonts(candidate_pdf)$embedded),
               canvas_mm=c(174,210),existing_word_placement_mm=c(154.69675,186.69),
               plot_source_input_unchanged=hash(input)=='8f41b544a299ebfa361732ff285762d7e87d407f8a4615d0ea6fd45f32515f26')
write_json(result,file.path(output,asset('_LEGEND_REPAIR_QA.json')),pretty=TRUE,auto_unbox=TRUE,digits=17)
print(result)

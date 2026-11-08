# Visual-only Figure 3 adapter. All scientific values and display strings are inherited.
# Usage: Rscript --vanilla render_fig3_legibility.R INPUT_RUN OUTPUT_DIR R_LIBRARY
args<-commandArgs(TRUE)
stopifnot(length(args)==3)
input<-normalizePath(args[1],winslash='/',mustWork=TRUE)
out<-normalizePath(args[2],winslash='/',mustWork=FALSE)
lib<-normalizePath(args[3],winslash='/',mustWork=TRUE)
if(dir.exists(out)||file.exists(out))stop('Output must be a new directory; preserve previous attempts')
if(startsWith(tolower(paste0(out,'/')),tolower(paste0(input,'/'))))stop('Output cannot be inside input run')
.libPaths(c(lib,.Library),include.site=FALSE)
suppressPackageStartupMessages({library(ggplot2);library(patchwork);library(grid);library(pdftools);library(jsonlite);library(digest);library(xml2)})
for(pkg in c('ragg','png','svglite'))stopifnot(requireNamespace(pkg,quietly=TRUE))
locale<-Sys.setlocale('LC_CTYPE','English_United States.utf8')
if(!nzchar(locale))stop('Required UTF-8 locale unavailable')
options(device=function(...)stop('UNPLANNED_DEFAULT_GRAPHICS_DEVICE'))
dir.create(out,recursive=TRUE)
hash<-function(p)digest(readBin(p,'raw',n=file.info(p)$size),algo='sha256',serialize=FALSE)
src<-file.path(input,'f23/06_FIGURE_3/Fig3_CURRENT_SOURCE_REPLAY_PLOT.rds')
csv<-file.path(input,'f23/formal/03_repaired_figure_sources/F2/FIG3_EXACT_DISPLAY_DATA.csv')
before<-c(plot=hash(src),csv=hash(csv))
old<-readRDS(src)
source_rows<-read.csv(csv,check.names=FALSE,fileEncoding='UTF-8-BOM',colClasses='character')
stopifnot(nrow(source_rows)==72,all(table(source_rows$sector)==36))
panels<-list(old[[1]],old[[2]])
stopifnot(all(vapply(panels,function(p)nrow(p$data)==36,logical(1))))
# Restore the inherited global theme; scientific scales/layers remain native.
theme_set(theme_classic(base_size=9,base_family='Arial')+
 theme(axis.line=element_line(linewidth=.3,colour='#353535'),axis.ticks=element_line(linewidth=.25),
 axis.text=element_text(colour='#202020',size=8),axis.title=element_text(size=9),
 strip.background=element_rect(fill='#F0F2F3',colour=NA),strip.text=element_text(size=9,face='italic'),
 legend.position='bottom',legend.text=element_text(size=9),legend.title=element_text(size=9),
 plot.margin=margin(3,3,3,3)))
newpanels<-lapply(seq_along(panels),function(i){
 p<-panels[[i]]
 stopifnot(length(p$layers)==2,inherits(p$layers[[2]]$geom,'GeomText'))
 # The existing label column is unchanged. Only the physical text size is adjusted.
 p$layers[[2]]$aes_params$size<-8/ggplot2::.pt
 p+theme(
   text=element_text(family='Arial',colour='#101010'),
   axis.text.x=element_text(angle=90,hjust=1,vjust=.5,face='italic',size=8.5,
                           margin=margin(t=2.2,unit='mm')),
   axis.text.y=element_text(face='italic',size=8.5,margin=margin(r=1.2,unit='mm')),
   plot.title=element_text(size=9.5,face='bold',hjust=0,margin=margin(b=2.6,unit='mm')),
   plot.title.position='panel',
   plot.margin=margin(t=3,r=if(i==1)1.5 else .5,b=2,l=if(i==1).5 else 1.5,unit='mm'),
   legend.position='bottom',legend.direction='horizontal',
   legend.title=element_text(size=9,margin=margin(b=2,unit='mm')),
   legend.text=element_text(size=8.5,margin=margin(t=1.4,unit='mm')),
   legend.box.margin=margin(t=3,r=0,b=1,l=0,unit='mm'),
   legend.key.width=unit(11,'mm'),legend.key.height=unit(3.2,'mm')
 )+guides(fill=guide_colourbar(title.position='top',title.hjust=.5,
                              label.position='bottom',barwidth=unit(60,'mm'),
                              barheight=unit(3.2,'mm'),ticks=TRUE))
})
plot<-wrap_plots(newpanels,nrow=1,widths=c(1,1),guides='collect')&
 theme(legend.position='bottom')
# Exact data and encoding lock, independent of allowed physical geometry.
checks<-list();rows<-list()
for(i in seq_along(panels)){
 a<-panels[[i]];b<-newpanels[[i]]
 ab<-ggplot_build(a);bb<-ggplot_build(b)
 stopifnot(identical(a$data,b$data))
 fieldsets<-list(c('x','y','xmin','xmax','ymin','ymax','fill','group','PANEL'),
                 c('x','y','label','colour','group','PANEL'))
 lc<-lapply(seq_along(fieldsets),function(k){
  fields<-intersect(fieldsets[[k]],names(ab$data[[k]]))
  stopifnot(all(fields %in% names(bb$data[[k]])))
  same<-identical(ab$data[[k]][fields],bb$data[[k]][fields])
  list(layer=k,fields=fields,exact=same)
 })
 as<-ab$plot$scales$get_scales('fill');bs<-bb$plot$scales$get_scales('fill')
 scale_same<-identical(as$limits,bs$limits)&&identical(as$breaks,bs$breaks)&&
  identical(as$labels,bs$labels)&&identical(as$map(seq(-1,1,length.out=201)),bs$map(seq(-1,1,length.out=201)))
 axis_same<-identical(ab$layout$panel_params[[1]]$x$breaks,bb$layout$panel_params[[1]]$x$breaks)&&
  identical(ab$layout$panel_params[[1]]$x$get_labels(),bb$layout$panel_params[[1]]$x$get_labels())&&
  identical(ab$layout$panel_params[[1]]$y$get_labels(),bb$layout$panel_params[[1]]$y$get_labels())
 stopifnot(all(vapply(lc,function(x)x$exact,logical(1))),scale_same,axis_same)
 d<-a$data;key<-paste(d$sector,d$species_a,d$species_b,sep='|')
 j<-match(key,paste(source_rows$sector,source_rows$species_a,source_rows$species_b,sep='|'))
 stopifnot(!anyNA(j),identical(as.character(d$lab),as.character(source_rows$lab[j])),
           max(abs(d$rho-as.numeric(source_rows$rho[j]))) < 1e-14)
 rows[[i]]<-data.frame(sector=d$sector,species_a=d$species_a,species_b=d$species_b,
                      source_rho=d$rho,candidate_rho=b$data$rho,
                      source_label=d$lab,candidate_label=b$data$lab,
                      source_n_events=d$n_paired_events,candidate_n_events=b$data$n_paired_events,
                      rho_exact=d$rho==b$data$rho,label_exact=d$lab==b$data$lab,
                      stringsAsFactors=FALSE)
 checks[[i]]<-list(panel=i,sector=unique(d$sector),n_events=unique(d$n_paired_events),
  data_exact=identical(a$data,b$data),layers=lc,fill_mapping_201_points_exact=scale_same,
  source_order_axis_labels_exact=axis_same)
}
write.csv(do.call(rbind,rows),file.path(out,'FIG3_EXACT_NUMERIC_COMPARISON.csv'),row.names=FALSE,fileEncoding='UTF-8')
# Apply typographic changes only after the inherited exact scientific lock.
minus <- function(x) gsub("-(?=[0-9])", "\u2212", x, perl=TRUE)
newpanels <- lapply(newpanels, function(p) {
 oldbuild <- ggplot_build(p)
 oldscale <- oldbuild$plot$scales$get_scales('fill')
 sc <- p$scales$get_scales('fill')
 sc$name <- 'Spearman \u03c1'
 sc$labels <- minus(oldscale$get_labels(oldscale$get_breaks()))
 p$data$lab <- minus(p$data$lab)
 updated <- ggplot_build(p)
 stopifnot(identical(oldbuild$data[[1]],updated$data[[1]]),
           identical(minus(oldbuild$data[[2]]$label),updated$data[[2]]$label),
           identical(oldbuild$data[[2]][setdiff(names(oldbuild$data[[2]]),'label')],
                     updated$data[[2]][setdiff(names(updated$data[[2]]),'label')]),
           identical(oldscale$map(seq(-1,1,length.out=201)),updated$plot$scales$get_scales('fill')$map(seq(-1,1,length.out=201))),
           identical(oldscale$get_breaks(),updated$plot$scales$get_scales('fill')$get_breaks()))
 p
})
plot <- wrap_plots(newpanels,nrow=1,widths=c(1,1),guides='collect') & theme(legend.position='bottom')
write.csv(do.call(rbind,lapply(newpanels,function(p) p$data[c('sector','species_a','species_b','rho','lab','n_paired_events')])),
          file.path(out,'F3_FINAL_RENDER_LABELS.csv'),row.names=FALSE,fileEncoding='UTF-8')
saveRDS(plot,file.path(out,'Fig3_LEGIBILITY_CANDIDATE_PLOT.rds'))
stem<-file.path(out,'Fig3_LEGIBILITY_CANDIDATE')
width<-174;height<-120
svglite::svglite(paste0(stem,'.svg'),width=width/25.4,height=height/25.4);print(plot);dev.off()
cairo_pdf(paste0(stem,'.pdf'),width=width/25.4,height=height/25.4,family='Arial');print(plot);dev.off()
cairo_ps(paste0(stem,'.eps'),width=width/25.4,height=height/25.4,family='Arial',onefile=FALSE,fallback_resolution=1200);print(plot);dev.off()
for(dpi in c(600,1200)){
 ragg::agg_tiff(paste0(stem,'_',dpi,'dpi.tiff'),width=width,height=height,units='mm',res=dpi,background='white',compression='lzw');print(plot);dev.off()
}
ragg::agg_png(paste0(stem,'_600dpi.png'),width=width,height=height,units='mm',res=600,background='white');print(plot);dev.off()
# These previews are generated by the R backend from the actual vector PDF.
for(dpi in c(96,150,300)){
 bitmap<-pdf_render_page(paste0(stem,'.pdf'),page=1,dpi=dpi)
 png::writePNG(bitmap,paste0(stem,'_PDF_',dpi,'dpi.png'),dpi=dpi)
}
tx<-pdf_data(paste0(stem,'.pdf'))[[1]];ps<-pdf_pagesize(paste0(stem,'.pdf'))
outside<-tx[tx$x < -0.01|tx$y < -0.01|tx$x+tx$width>ps$width+.01|tx$y+tx$height>ps$height+.01,]
# Bounds are a technical check; independent final-size visual review remains required.
stopifnot(nrow(outside)==0,all(pdf_fonts(paste0(stem,'.pdf'))$embedded))
write.csv(tx,file.path(out,'FIG3_PDF_TEXT_BOUNDS.csv'),row.names=FALSE,fileEncoding='UTF-8')
after<-c(plot=hash(src),csv=hash(csv));stopifnot(identical(before,after))
write_json(list(status='NATIVE_DATA_ENCODING_LOCK_PASSED_VISUAL_REVIEW_REQUIRED',
 source_hashes=before,source_files_unchanged=identical(before,after),
 original_source_read_no_estimation=TRUE,coefficients=72,panels=checks,
 physical_mm=c(width=width,height=height),fonts=pdf_fonts(paste0(stem,'.pdf')),
 pdf_text_outside_page=nrow(outside),runtime=R.version.string,
 packages=setNames(lapply(c('ggplot2','patchwork','svglite','ragg','pdftools'),function(x)as.character(packageVersion(x))),c('ggplot2','patchwork','svglite','ragg','pdftools')),
 author_approval='REQUIRED'),file.path(out,'FIG3_DATA_ENCODING_QA.json'),pretty=TRUE,auto_unbox=TRUE)
cat('FIG3_VISUAL_ADAPTER_COMPLETE_72_EXACT_VALUES_AND_LABELS\n')

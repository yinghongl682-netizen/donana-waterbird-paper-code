# Figure 4 presentation-only repair. Scientific source remains the inherited renderer.
# Usage: Rscript --vanilla render_fig4_legibility.R --input-run RUN --output NEWDIR --r-library LIB [--original-source FILE]
args<-commandArgs(TRUE)
getarg<-function(k,required=TRUE,default=NULL){i<-match(k,args);if(is.na(i)){if(required)stop('Missing ',k);return(default)};if(i==length(args))stop('Missing value ',k);args[i+1]}
lib<-getarg('--r-library');.libPaths(c(normalizePath(lib,winslash='/',mustWork=TRUE),.Library),include.site=FALSE)
suppressPackageStartupMessages({library(ggplot2);library(patchwork);library(grid);library(jsonlite);library(digest);library(pdftools);library(png);library(magick);library(colorspace);library(xml2)})
loc<-Sys.setlocale('LC_CTYPE','English_United States.utf8');if(!nzchar(loc))stop('Required inherited UTF-8 locale unavailable')
options(warn=1,device=function(...)stop('Unplanned graphics device'))
run<-normalizePath(getarg('--input-run'),winslash='/',mustWork=TRUE)
out<-getarg('--output')
if(dir.exists(out)||file.exists(out))stop('Output must be a new directory; preserve prior attempts')
scriptdir<-dirname(normalizePath(sub('^--file=','',grep('^--file=',commandArgs(),value=TRUE)[1]),winslash='/',mustWork=TRUE))
sourcefile<-getarg('--original-source',FALSE,file.path(scriptdir,'render_fig4.R'))
sourcefile<-normalizePath(sourcefile,winslash='/',mustWork=TRUE)
out<-normalizePath(out,winslash='/',mustWork=FALSE)
if(startsWith(tolower(out),paste0(tolower(run),'/'))||startsWith(tolower(out),paste0(tolower(scriptdir),'/')))stop('Use external new output folder')
dir.create(out,recursive=TRUE);for(s in c('qa','exports','data_lock'))dir.create(file.path(out,s))
hash<-function(p)digest(readBin(p,'raw',n=file.info(p)$size),algo='sha256',serialize=FALSE)
src<-readLines(sourcefile,encoding='UTF-8',warn=FALSE)
begin<-grep('^hash<-function',src);end<-grep('^F4<-',src)
stopifnot(length(begin)==1,length(end)==1,begin<end)
# Evaluate the unmodified original scientific layer construction, stopping before any old exports.
OUTPUT_ROOT<-run;O<-file.path(run,'r2/04_MAIN_FIGURES_AND_TABLES/plot_data');B<-out;S<-out
eval(parse(text=src[begin:(end-1)]),envir=.GlobalEnv)
original_a<-a;original_b<-b;original_c<-c
old_a<-ggplot_build(a);old_b<-ggplot_build(b);old_c<-ggplot_build(c)
old_legend_svg<-file.path(run,'fig4/figures/FIG4_L1_DIAMOND_LEGEND.svg')
stopifnot(file.exists(old_legend_svg))
oldtext<-xml_text(xml_find_all(read_xml(old_legend_svg),'.//*[local-name()="text"]'))
# Bind already-approved strings; no revised rounding rule is introduced.
stopifnot(all(small$label%in%oldtext))
old_cq_label<-old_a$data[[9]]$label
stopifnot(length(old_cq_label)==1,old_cq_label%in%oldtext,identical(old_cq_label,'Cq = -0.085'))
original_inputs<-data.frame(path=inputs,sha256=unname(before),stringsAsFactors=FALSE)
write.csv(original_inputs,file.path(out,'data_lock/INPUT_IDENTITIES.csv'),row.names=FALSE,fileEncoding='UTF-8')
base_theme<-theme(text=element_text(family='Arial',size=8.5,colour=ink),
 axis.text=element_text(size=8.5,colour=ink),
 axis.title=element_text(size=8.5,colour=ink),
 axis.title.x=element_text(margin=margin(t=2.0,unit='mm')),
 plot.title=element_text(size=9.5,face='bold',margin=margin(b=2,unit='mm')),
 plot.tag=element_text(size=10,face='bold'),plot.tag.position=c(0,1),
 plot.margin=margin(2,4,2,3,unit='mm'),
 legend.text=element_text(size=8.5),legend.title=element_text(size=8.5),
 legend.margin=margin(0,0,0,0),legend.box.spacing=unit(1.5,'mm'),
 legend.key.height=unit(3.0,'mm'),legend.key.width=unit(4.0,'mm'))
a<-a+base_theme+theme(legend.position='top',legend.box='vertical',legend.spacing.y=unit(.4,'mm'),
 axis.text.y=element_text(face='italic',size=8.5),legend.box.just='left')+
 guides(fill=guide_legend(order=1,nrow=1))
# The original point layer now participates in a real guide; its shape and coordinates are unchanged.
a$layers[[5]]$mapping$shape<-rlang::new_quosure(quote('Net change'),env=rlang::empty_env())
a$layers[[5]]$aes_params$shape<-NULL
a<-a+scale_shape_manual(values=c('Net change'=23),labels=expression(paste('Net change (',Delta,mu,'; panels a–b)')),name=NULL)+
 guides(shape=guide_legend(order=2,override.aes=list(fill=ink,colour='white',size=2.5)))
# Original bar-internal labels retain content and coordinates; typography changes only.
for(k in 6:8)a$layers[[k]]$aes_params$size<-8.5/ggplot2::.pt
a$layers[[9]]$aes_params$size<-8.5/ggplot2::.pt
a$layers[[9]]$data$x<- -9.0
# This callout is anchored to the thin Netta Cq rectangle's upper edge, not to a moved net diamond.
cqrow<-old_a$data[[1]][old_a$data[[1]]$fill==orange & old_a$data[[1]]$y==1,]
stopifnot(nrow(cqrow)==1)
cq_target<-c(x=(cqrow$xmin+cqrow$xmax)/2,y=cqrow$ymax)
a<-a+annotate('segment',x=-8.8,xend=cq_target[['x']],y=1.04,yend=cq_target[['y']],linewidth=.2,colour=ink)
b<-b+base_theme+theme(axis.text.y=element_text(face='italic',size=8.5),legend.position='bottom',legend.direction='horizontal')+
 guides(fill=guide_legend(nrow=1))
b$layers[[5]]$aes_params$size<-8.5/ggplot2::.pt
b$layers[[5]]$aes_params$label.padding<-unit(.35,'mm')
c<-c+base_theme+theme(axis.text.x=element_text(angle=0,hjust=.5,size=8.5,margin=margin(t=1.5,unit='mm')),
 axis.text.y=element_text(face='italic',size=8.5),legend.position='bottom',
 legend.title=element_text(size=8.5,margin=margin(b=2,unit='mm')),
 legend.text=element_text(size=8.5))+
 guides(fill=guide_colourbar(title.position='top',title.hjust=.5,
 barwidth=unit(75,'mm'),barheight=unit(3,'mm'),ticks.colour='grey45',
 theme=theme(legend.title.position='top',legend.spacing.y=unit(2,'mm'))))
c$layers[[2]]$aes_params$size<-8.5/ggplot2::.pt
new_a<-ggplot_build(a);new_b<-ggplot_build(b);new_c<-ggplot_build(c)
samecols<-function(x,y,ks)all(vapply(ks,function(k)isTRUE(all.equal(x[[k]],y[[k]],tolerance=0,check.attributes=FALSE)),logical(1)))
locks<-list(
 a_bar_rectangles_and_fill=samecols(old_a$data[[1]],new_a$data[[1]],c('xmin','xmax','ymin','ymax','fill')),
 a_zero_line=samecols(old_a$data[[2]],new_a$data[[2]],c('xintercept')),
 a_net_diamond_xy_shape=samecols(old_a$data[[5]],new_a$data[[5]],c('x','y','shape','fill','colour')),
 a_hatch_geometry_identical=identical(original_a$layers[[3]]$data,a$layers[[3]]$data)&&identical(original_a$layers[[4]]$data,a$layers[[4]]$data),
 a_all_internal_label_strings=identical(unlist(lapply(old_a$data[6:9],function(z)z$label)),unlist(lapply(new_a$data[6:9],function(z)z$label))),
 b_bars_and_fill=samecols(old_b$data[[2]],new_b$data[[2]],c('xmin','xmax','ymin','ymax','fill')),
 b_net_diamond_xy_shape=samecols(old_b$data[[4]],new_b$data[[4]],c('x','y','shape','fill','colour')),
 b_leaders_xy=samecols(old_b$data[[3]],new_b$data[[3]],c('x','xend','y','yend')),
 b_five_signed_labels=samecols(old_b$data[[5]],new_b$data[[5]],c('x','y','label')),
 c_20_tiles_and_fill=samecols(old_c$data[[1]],new_c$data[[1]],c('xmin','xmax','ymin','ymax','fill')),
 c_20_original_label_strings=samecols(old_c$data[[2]],new_c$data[[2]],c('x','y','label','colour')),
 axis_ranges=all(vapply(list(list(old_a,new_a),list(old_b,new_b),list(old_c,new_c)),function(z)identical(z[[1]]$layout$panel_params[[1]]$x.range,z[[2]]$layout$panel_params[[1]]$x.range)&&identical(z[[1]]$layout$panel_params[[1]]$y.range,z[[2]]$layout$panel_params[[1]]$y.range),logical(1))))
write_json(locks,file.path(out,'qa/F4_SCIENTIFIC_ENCODING_LOCK.json'),pretty=TRUE,auto_unbox=TRUE)
stopifnot(all(unlist(locks)))
# Replace numerical sign glyphs after preserving original analytical strings.
minus <- function(x) gsub("-(?=[0-9])", "\u2212", x, perl=TRUE)
minus_labels <- function(x) minus(scales::label_number()(x))
a$layers[[9]]$aes_params$label <- minus(a$layers[[9]]$aes_params$label)
b$layers[[5]]$data$label <- minus(b$layers[[5]]$data$label)
c$data$label <- minus(c$data$label)
for (which in c('a','b')) {
 p <- get(which)
 sc <- p$scales$get_scales('x')
 if(is.null(sc))p <- p+scale_x_continuous(labels=minus_labels) else sc$labels <- minus_labels
 p$scales$get_scales('shape') -> shp
 if(!is.null(shp))shp$labels <- 'Net change (\u0394\u03bc; panels a\u2013b)'
 assign(which,p)
}
check_display <- function(before, after, labelled) {
 stopifnot(length(before$data)==length(after$data))
 for(k in seq_along(before$data)){
   cols <- setdiff(names(before$data[[k]]),if(k %in% labelled)'label' else character())
   stopifnot(identical(before$data[[k]][cols],after$data[[k]][cols]))
   if(k %in% labelled)stopifnot(identical(minus(before$data[[k]]$label),after$data[[k]]$label))
 }
 stopifnot(identical(before$layout$panel_params[[1]]$x.range,after$layout$panel_params[[1]]$x.range))
 TRUE
}
final_a <- ggplot_build(a); final_b <- ggplot_build(b); final_c <- ggplot_build(c)
# Explicit tick text is set from the old trained values to avoid an incidental precision change.
for (which in c('a','b')) {
 p <- get(which)
 z <- if(which=='a')new_a else new_b
 old_axis <- z$layout$panel_params[[1]]$x
 xscale <- p$scales$get_scales('x')
 xscale$breaks <- old_axis$get_breaks()
 xscale$labels <- minus(old_axis$get_labels())
 assign(which,p)
}
old_fill <- new_c$plot$scales$get_scales('fill')
fill_scale <- c$scales$get_scales('fill')
fill_scale$breaks <- old_fill$get_breaks()
fill_scale$labels <- minus(old_fill$get_labels(old_fill$get_breaks()))
final_a <- ggplot_build(a); final_b <- ggplot_build(b); final_c <- ggplot_build(c)
display_lock <- c(a=check_display(new_a,final_a,9),b=check_display(new_b,final_b,5),c=check_display(new_c,final_c,2))
stopifnot(identical(minus(new_a$layout$panel_params[[1]]$x$get_labels()),final_a$layout$panel_params[[1]]$x$get_labels()),
          identical(minus(new_b$layout$panel_params[[1]]$x$get_labels()),final_b$layout$panel_params[[1]]$x$get_labels()),
          identical(minus(old_fill$get_labels(old_fill$get_breaks())),final_c$plot$scales$get_scales('fill')$get_labels()))
write_json(list(display_checks=display_lock,sign='U+2212',net_legend='Net change (\u0394\u03bc; panels a\u2013b)'),
           file.path(out,'qa/F4_FINAL_RENDER_DISPLAY_LOCK.json'),auto_unbox=TRUE,pretty=TRUE)
F4<-(a/b/c)+plot_layout(heights=c(1,1.85,1.2))
width_mm<-174;height_mm<-205
stem<-file.path(out,'exports/Fig4_LEGIBILITY_CANDIDATE')
draw<-function()print(F4)
ragg::agg_png(paste0(stem,'_600dpi.png'),width=width_mm,height=height_mm,units='mm',res=600,background='white');draw();dev.off()
ragg::agg_png(paste0(stem,'_300dpi.png'),width=width_mm,height=height_mm,units='mm',res=300,background='white');draw();dev.off()
svglite::svglite(paste0(stem,'.svg'),width=width_mm/25.4,height=height_mm/25.4);draw();dev.off()
cairo_pdf(paste0(stem,'.pdf'),width=width_mm/25.4,height=height_mm/25.4,family='Arial');draw();dev.off()
ragg::agg_tiff(paste0(stem,'_600dpi.tiff'),width=width_mm,height=height_mm,units='mm',res=600,background='white',compression='lzw');draw();dev.off()
saveRDS(list(a=a,b=b,c=c,figure=F4),paste0(stem,'_PLOTS.rds'))
for(dpi in c(96,150,300))png::writePNG(pdf_render_page(paste0(stem,'.pdf'),dpi=dpi),file.path(out,'qa',paste0('F4_PDF_',dpi,'dpi.png')),dpi=dpi)
fonts<-pdf_fonts(paste0(stem,'.pdf'));tx<-pdf_data(paste0(stem,'.pdf'))[[1]];psz<-pdf_pagesize(paste0(stem,'.pdf'))
bounds<-tx[tx$x < -0.02 | tx$y < -0.02 | tx$x+tx$width>psz$width+.02 | tx$y+tx$height>psz$height+.02,]
# Export factual bounds; visual approval is separate.
write.csv(tx,file.path(out,'qa/PDF_TEXT_BOUNDS.csv'),row.names=FALSE,fileEncoding='UTF-8')
write_json(list(width_mm=width_mm,height_mm=height_mm,fonts=fonts,outside_count=nrow(bounds),rendering='R-only; original scientific source reused',source_sha256=hash(sourcefile),source_inputs_unchanged=identical(unname(before),unname(sapply(inputs,hash))),all_scientific_encoding_checks=all(unlist(locks)),author_approval='REQUIRED',visual_review='PENDING',r=R.version.string,packages=capture.output(sessionInfo())),file.path(out,'qa/F4_EXPORT_RECEIPT.json'),pretty=TRUE,auto_unbox=TRUE)
stopifnot(nrow(bounds)==0,all(fonts$embedded),identical(unname(before),unname(sapply(inputs,hash))))
for(item in list(list('a_rectangles',old_a$data[[1]],new_a$data[[1]],c('xmin','xmax','ymin','ymax','fill')),
 list('a_net',old_a$data[[5]],new_a$data[[5]],c('x','y','shape')),
 list('b_rectangles',old_b$data[[2]],new_b$data[[2]],c('xmin','xmax','ymin','ymax','fill')),
 list('b_net',old_b$data[[4]],new_b$data[[4]],c('x','y','shape')),
 list('c_tiles',old_c$data[[1]],new_c$data[[1]],c('xmin','xmax','ymin','ymax','fill')),
 list('c_labels',old_c$data[[2]],new_c$data[[2]],c('x','y','label','colour')))){
 write.csv(item[[2]][item[[4]]],file.path(out,'data_lock',paste0(item[[1]],'_original.csv')),row.names=FALSE,fileEncoding='UTF-8')
 write.csv(item[[3]][item[[4]]],file.path(out,'data_lock',paste0(item[[1]],'_candidate.csv')),row.names=FALSE,fileEncoding='UTF-8')
}
cat('F4_PRESENTATION_REPAIR_EXPORTED; SCIENTIFIC_VALUES_LOCKED; VISUAL_REVIEW_PENDING\n')

# Figure 5 typography-only adapter derived from the preserved P1 renderer.
# Usage: Rscript --vanilla render_fig5_figpolish.R PLOT_DATA_DIR NEW_OUTPUT_DIR R_LIBRARY
args <- commandArgs(trailingOnly=TRUE)
if (length(args)!=3L) stop('Expected plot data, new output, and R library paths')
D <- normalizePath(args[1],winslash='/',mustWork=TRUE)
if (file.exists(args[2])) stop('Output directory already exists')
dir.create(args[2],recursive=TRUE)
O <- normalizePath(args[2],winslash='/',mustWork=TRUE)
lib <- normalizePath(args[3],winslash='/',mustWork=TRUE)
.libPaths(c(lib,.Library),include.site=FALSE)
locale_value <- Sys.setlocale('LC_CTYPE','English_United States.utf8')
if (!nzchar(locale_value)) stop('UTF-8 locale unavailable')
options(warn=1,device=function(...)stop('UNPLANNED_DEFAULT_GRAPHICS_DEVICE_BLOCKED'))
suppressPackageStartupMessages({library(ggplot2);library(patchwork);library(grid);library(jsonlite);library(digest);library(pdftools);library(png)})
script_file <- sub('^--file=','',grep('^--file=',commandArgs(FALSE),value=TRUE))
original_script <- file.path(dirname(normalizePath(script_file,winslash='/')),'render_fig5_p1_original.R')
hash<-function(p)digest(readBin(p,'raw',n=file.info(p)$size),algo='sha256',serialize=FALSE)
ids<-c('F5a_ANNUAL_NAMED_LOCALITY_RECORDS','F5a_PERIOD_MEAN_SEGMENTS','F5b_PERIOD_LOCALITY_CHANGES','F5c_CONCENTRATION_TIME_OBJECTS')
inputs<-file.path(D,paste0(ids,'.csv'));before<-sapply(inputs,hash)
rd<-function(p)read.csv(p,check.names=FALSE,stringsAsFactors=FALSE,fileEncoding='UTF-8-BOM')
a<-rd(inputs[1]);m<-rd(inputs[2]);b<-rd(inputs[3]);cc<-rd(inputs[4])
blue<-'#2166AC';orange<-'#B35806';ink<-'#272727'
type_system <- theme_classic(base_size=9,base_family='Arial')+
  theme(axis.text=element_text(size=8.5,colour=ink),
        axis.title=element_text(size=9,margin=margin(t=3)),
        axis.title.y=element_text(size=9,margin=margin(r=4)),
        axis.line=element_line(linewidth=.3),axis.ticks=element_line(linewidth=.3),
        strip.text=element_text(size=9,face='bold',lineheight=.95,margin=margin(3,4,3,4)),
        strip.background=element_rect(fill='#F0F2F3',colour=NA),
        legend.title=element_text(size=9),legend.text=element_text(size=8.5),
        legend.position='bottom',legend.margin=margin(0,0,0,0),
        legend.box.margin=margin(0,0,0,0),legend.spacing.x=unit(2,'mm'),
        legend.key.height=unit(4,'mm'),plot.tag=element_text(size=10,face='bold'),
        plot.tag.position=c(0,1),plot.margin=margin(3,4,3,3),
        panel.spacing=unit(4,'mm'),panel.grid=element_blank())
theme_set(type_system)
minus <- function(x) sub('^-','−',x)
period_text <- function(x) sub('^([0-9]{4})-([0-9]{4})','\\1–\\2',x)
axis_minus <- function(x) minus(scales::label_number()(x))

p5a<-ggplot(a,aes(year,Y))+annotate('rect',xmin=2017.5,xmax=2023.3,ymin=-Inf,ymax=Inf,fill='#F1F2F3')+geom_line(linewidth=.35)+geom_point(size=1.2)+geom_segment(data=m,aes(x=start,xend=end,y=Y,yend=Y,colour=period,linetype=period),inherit.aes=FALSE,linewidth=.7)+facet_wrap(~case,nrow=1,scales='free_y')+scale_x_continuous(breaks=c(2013,2018,2023))+scale_colour_manual(values=c(blue,orange),labels=period_text)+scale_linetype_manual(values=c('dashed','solid'),labels=period_text)+labs(x='Calendar year',y='Annual locality Y',colour=NULL,linetype=NULL)+theme(legend.position='bottom')
pn<-c('Rocío','Dehesa','Gavetas','Balsas AB');lev<-unlist(lapply(c('Coot','Pochard'),function(s)paste(s,pn,sep=' / ')))
b$case<-factor(b$case,levels=rev(lev))
bb<-rbind(data.frame(case=b$case,value=b$annual_network_contribution,metric='Network mean contribution'),data.frame(case=b$case,value=b$delta_W*100,metric='Share change (percentage points)'))
b0<-ggplot(bb,aes(value,case))+geom_vline(xintercept=0,colour='grey65',linewidth=.35)+geom_point(shape=16,size=1.8,colour=blue)+facet_wrap(~metric,nrow=1,scales='free_x')+labs(x=NULL,y=NULL)+theme(legend.position='none')
bl<-bb[bb$case=='Pochard / Rocío',];bl$label<-sprintf('%+.3f',bl$value);stopifnot(nrow(bl)==2,all(bl$value<0))
bl$label <- minus(bl$label)
bl$label_x <- ifelse(bl$metric=='Network mean contribution',-.72,-.62)
bl$leader_x <- bl$label_x + ifelse(bl$metric=='Network mean contribution',.16,.13)
bl$leader_end <- bl$value-ifelse(bl$metric=='Network mean contribution',.12,.10)
p5b<-b0+geom_segment(data=bl,aes(x=leader_x,xend=leader_end,y=case,yend=case),
                     linewidth=.24,colour='grey42',inherit.aes=FALSE)+
  geom_text(data=bl,aes(x=label_x,label=label),hjust=1,size=8.5/ggplot2::.pt,family='Arial')+
  scale_x_continuous(labels=axis_minus)+
  facet_wrap(~metric,nrow=1,scales='free_x',
             labeller=as_labeller(c('Network mean contribution'='Contribution\n(counts per slot)',
                                    'Share change (percentage points)'='Share change\n(percentage points)')))

cc$sp<-factor(cc$sp,levels=c('N. rufina','F. atra'));cc$object<-factor(cc$object,levels=c('endpoint','period','annual_mean'))
makec<-function(dark=FALSE){ggplot(cc,aes(delta,sp,shape=object,colour=object))+geom_vline(xintercept=0,colour='grey65',linewidth=.35)+geom_point(position=position_dodge(width=.55),size=2.2,stroke=if(dark).75 else .5)+facet_wrap(~level,nrow=1,labeller=as_labeller(c(child='Child level',parent='Parent level')))+scale_shape_manual(values=c(1,16,17),labels=c('2013–2023 endpoints','Period-average distribution','Mean annual HHI'))+scale_colour_manual(values=c(if(dark)'#4C4C4C'else'grey50',blue,orange),labels=c('2013–2023 endpoints','Period-average distribution','Mean annual HHI'))+scale_x_continuous(labels=axis_minus)+labs(x='HHI change',y=NULL,shape=NULL,colour=NULL)+theme(legend.position='bottom',legend.key.width=unit(4,'mm'),axis.text.y=element_text(face='italic'))}
c0<-makec();p5c<-makec(TRUE)
# Match the two stored near-zero values to the full original dodged layer before adding annotations.
cb<-ggplot_build(c0);pts<-cb$data[[2]];layout<-cb$layout$layout
labels<-cc[(cc$species=='Fulica atra'&cc$level=='parent'&cc$object=='annual_mean')|(cc$species=='Netta rufina'&cc$level=='child'&cc$object=='period'),]
labels$y<-vapply(seq_len(nrow(labels)),function(i){pp<-as.integer(layout$PANEL[layout$level==labels$level[i]]);hit<-pts[as.integer(pts$PANEL)==pp&abs(pts$x-labels$delta[i])<1e-14,];stopifnot(nrow(hit)==1);hit$y},numeric(1))
labels$label<-minus(sprintf('%+.6f',labels$delta));labels$label_x<-ifelse(labels$level=='parent',.009,.015)
p5c<-p5c+geom_text(data=labels,aes(x=label_x,y=y,label=label),inherit.aes=FALSE,hjust=0,size=8.5/ggplot2::.pt,family='Arial')
same<-function(x,y,cols)all(vapply(cols,function(z)isTRUE(all.equal(x[[z]],y[[z]],tolerance=0,check.attributes=FALSE)),logical(1)))
newb<-ggplot_build(p5b);newc<-ggplot_build(p5c)

# Rebuild the inherited plot objects from the verbatim source and same frozen CSVs.
# The private original's I/O and graphic export lines are never evaluated here.
source_lines <- readLines(original_script,encoding='UTF-8',warn=FALSE)
first <- grep('^hash<-function',source_lines)
last <- grep('^ck<-list',source_lines)-1L
stopifnot(length(first)==1L,length(last)==1L)
baseline_lines <- source_lines[first:last]
baseline_lines <- baseline_lines[!grepl('^for\\(p in inputs\\)',baseline_lines)]
reference <- new.env(parent=environment())
reference$D <- D
old_theme <- theme_get()
eval(parse(text=baseline_lines),envir=reference)
theme_set(old_theme)
compare_plot <- function(before_plot,after_plot,layer_ids) {
  old <- ggplot_build(before_plot); revised <- ggplot_build(after_plot)
  layer_keys <- c('x','y','xend','yend','xmin','xmax','ymin','ymax','PANEL','group',
                  'shape','colour','fill','linetype','size','stroke','linewidth','alpha')
  layer_check <- vapply(layer_ids,function(i) {
    left <- old$data[[i]]; right <- revised$data[[i]]
    fields <- intersect(layer_keys,names(left))
    nrow(left)==nrow(right) && same(left,right,fields)
  },logical(1))
  ranges <- vapply(seq_along(old$layout$panel_params),function(i){
    left<-old$layout$panel_params[[i]];right<-revised$layout$panel_params[[i]]
    identical(left$x.range,right$x.range)&&identical(left$y.range,right$y.range)&&
      identical(left$x$breaks,right$x$breaks)&&identical(left$y$breaks,right$y$breaks)
  },logical(1))
  list(data_layer_coordinates_and_encodings=as.list(layer_check),axis_ranges_and_breaks=as.list(ranges),
       panel_order_identical=identical(old$layout$layout,revised$layout$layout),row_counts=vapply(old$data[layer_ids],nrow,integer(1)))
}
locks <- list(a=compare_plot(reference$p5a,p5a,1:4),b=compare_plot(reference$p5b,p5b,1:2),
              c=compare_plot(reference$p5c,p5c,1:2))
for (panel in locks) stopifnot(all(unlist(panel$data_layer_coordinates_and_encodings)),
                              all(unlist(panel$axis_ranges_and_breaks)),panel$panel_order_identical)
stopifnot(identical(unname(before),unname(sapply(inputs,hash))))
F5 <- (p5a/p5b/p5c)+plot_layout(heights=c(1.05,1.20,.80))+plot_annotation(tag_levels='a')
width <- 174
height <- 203
base <- file.path(O,'FIG5_POLISH')
export <- function(device,filename,...) {
  device(filename,...)
  on.exit(dev.off())
  print(F5)
}
export(svglite::svglite,paste0(base,'.svg'),width=width/25.4,height=height/25.4,bg='white')
export(grDevices::cairo_pdf,paste0(base,'.pdf'),width=width/25.4,height=height/25.4,family='Arial')
export(grDevices::svg,paste0(base,'_WORD.svg'),width=width/25.4,height=height/25.4,onefile=TRUE,family='Arial')
export(ragg::agg_png,paste0(base,'_600dpi.png'),width=width,height=height,units='mm',res=600,background='white')
for (dpi in c(96,150,300)) {
  writePNG(pdf_render_page(paste0(base,'.pdf'),dpi=dpi),file.path(O,paste0('F5_PROOF_',dpi,'dpi.png')),dpi=dpi)
}
write_json(list(backend='R/ggplot2/patchwork/grid',original_source_sha256=hash(original_script),
                width_mm=width,height_mm=height,input_hashes=as.list(setNames(before,basename(inputs))),
                source_inputs_unchanged=TRUE,locks=locks,
                b_labels=bl[,c('case','metric','value','label')],
                c_labels=labels[,c('species','level','object','delta','y','label')],
                expected_support='702 positions',session=capture.output(sessionInfo())),
           file.path(O,'F5_SCIENTIFIC_LOCK.json'),pretty=TRUE,auto_unbox=TRUE,digits=17)
cat('Figure 5 typography and baseline plot locks complete.\n')

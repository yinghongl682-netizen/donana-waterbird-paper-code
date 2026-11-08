# Compare scientific plot objects without treating serialized environment bytes as data.
args<-commandArgs(TRUE)
stopifnot(length(args)==4)
.libPaths(c(normalizePath(args[3],winslash='/',mustWork=TRUE),.Library),include.site=FALSE)
stopifnot(nzchar(Sys.setlocale('LC_CTYPE','English_United States.utf8')))
suppressPackageStartupMessages({library(ggplot2);library(jsonlite);library(digest)})
ref<-readRDS(args[1]);fresh<-readRDS(args[2])
stopifnot(inherits(ref,'ggplot'),inherits(fresh,'ggplot'),length(ref$layers)==6,length(fresh$layers)==6)
theme_set(theme_classic(base_size=9,base_family='Arial')+theme(
 axis.line=element_line(linewidth=.3,colour='#353535'),axis.ticks=element_line(linewidth=.25),
 axis.text=element_text(colour='#202020',size=8),axis.title=element_text(size=9),
 strip.background=element_rect(fill='#F0F2F3',colour=NA),strip.text=element_text(size=9,face='italic'),
 legend.position='bottom',legend.text=element_text(size=9),legend.title=element_text(size=9),
 plot.margin=margin(3,3,3,3)))
a<-ggplot_build(ref);b<-ggplot_build(fresh)
mapping<-function(x)lapply(x,function(y)paste(deparse(rlang::quo_get_expr(y)),collapse=''))
axis<-function(z)lapply(z$layout$panel_params,function(p)list(
 x_breaks=p$x$get_breaks(),x_labels=p$x$get_labels(),x_limits=p$x$limits,
 y_breaks=p$y$get_breaks(),y_labels=p$y$get_labels(),y_limits=p$y$limits))
checks<-list(
 raw_plot_data=identical(ref$data,fresh$data),
 plot_mapping=identical(mapping(ref$mapping),mapping(fresh$mapping)),
 layer_raw_data=all(vapply(seq_along(ref$layers),function(i)identical(ref$layers[[i]]$data,fresh$layers[[i]]$data),logical(1))),
 layer_mapping=all(vapply(seq_along(ref$layers),function(i)identical(mapping(ref$layers[[i]]$mapping),mapping(fresh$layers[[i]]$mapping)),logical(1))),
 layer_geom_types=identical(lapply(ref$layers,function(x)class(x$geom)),lapply(fresh$layers,function(x)class(x$geom))),
 layer_stat_types=identical(lapply(ref$layers,function(x)class(x$stat)),lapply(fresh$layers,function(x)class(x$stat))),
 built_six_layer_data=identical(a$data,b$data),
 panel_layout=identical(a$layout$layout,b$layout$layout),
 axis_values_and_labels=identical(axis(a),axis(b)))
hash<-function(p)digest(readBin(p,'raw',n=file.info(p)$size),algo='sha256',serialize=FALSE)
report<-list(status=if(all(unlist(checks)))'PLOT_SEMANTICS_EXACT' else 'FAIL',
 reference_rds_sha256=hash(args[1]),fresh_rds_sha256=hash(args[2]),checks=checks,
 scope='Plot data, mappings, six built layers and axes only. Serialized environments are not declared equal; original frozen artifact guard remains unchanged.')
write_json(report,args[4],pretty=TRUE,auto_unbox=TRUE)
stopifnot(all(unlist(checks)))
cat('PLOT_SEMANTICS_EXACT\n')

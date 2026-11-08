# Public I/O adapter: scientific plot bodies remain inherited.
local({
  lib <- Sys.getenv('DONANA_REPLAY_RLIB')
  if(!nzchar(lib) || !dir.exists(lib)) stop('DONANA_REPLAY_RLIB must name the isolated R package library')
  .libPaths(c(normalizePath(lib,winslash='/',mustWork=TRUE),.Library),include.site=FALSE)
})
out_value <- Sys.getenv('DONANA_OUTPUT_ROOT')
in_value <- Sys.getenv('DONANA_INPUT_ROOT')
if(!nzchar(out_value) || !nzchar(in_value)) stop('Set DONANA_OUTPUT_ROOT and DONANA_INPUT_ROOT')
dir.create(out_value,recursive=TRUE,showWarnings=FALSE)
OUTPUT_ROOT <- normalizePath(out_value,winslash='/',mustWork=TRUE)
INPUT_ROOT <- normalizePath(in_value,winslash='/',mustWork=TRUE)
if(identical(tolower(OUTPUT_ROOT),tolower(INPUT_ROOT))) stop('Input and output roots must differ')
locale_value <- Sys.setlocale('LC_CTYPE','English_United States.utf8')
if(!nzchar(locale_value)) stop('The inherited UTF-8 locale is unavailable; do not silently alter figure typography')
options(warn=1,device=function(...)stop('UNPLANNED_DEFAULT_GRAPHICS_DEVICE_BLOCKED'))

suppressPackageStartupMessages({library(ggplot2);library(patchwork);library(grid);library(jsonlite);library(digest);library(pdftools);library(png);library(magick);library(colorspace)})
B<-file.path(OUTPUT_ROOT,'fig4')
O<-file.path(OUTPUT_ROOT,'r2/04_MAIN_FIGURES_AND_TABLES/plot_data')
S<-B
for(p in c(B,file.path(B,'support/render_comparison'),file.path(B,'figures'),file.path(B,'diff')))dir.create(p,recursive=TRUE,showWarnings=FALSE)
hash<-function(p)digest(readBin(p,'raw',n=file.info(p)$size),algo='sha256',serialize=FALSE)
inputs<-c(file.path(O,c('F4a_GLOBAL_COMPONENTS.csv','F4b_POSITION_SIGNED_MASSES.csv','F4c_WEIGHTED_WINDOW_CONTRIBUTIONS.csv')),file.path(OUTPUT_ROOT,'bridge/results/ground/ANNUAL_CHANGE_SUMMARY.csv'))
before<-sapply(inputs,hash)
rd<-function(p)read.csv(p,check.names=FALSE,stringsAsFactors=FALSE,fileEncoding='UTF-8-BOM')
cmp<-rd(inputs[1]);mass<-rd(inputs[2]);win<-rd(inputs[3]);annual<-rd(inputs[4])
short<-function(x)sub('^([A-Za-z])[a-z]+ ','\\1. ',x)
focal<-c('Fulica atra','Netta rufina');selected<-c(focal,'Phoenicopterus roseus','Platalea leucorodia','Phalacrocorax carbo')
cmp$sp<-factor(cmp$sp,levels=rev(short(focal)))
annual$sp<-factor(short(annual$species),levels=rev(short(annual$species)))
mass$sp<-factor(mass$sp,levels=levels(annual$sp));win$sp<-factor(win$sp,levels=rev(short(selected)));win$window<-factor(win$window,levels=c('DJF','MarMay','JunJul','SON'))
aa<-annual[annual$species%in%focal,];aa$sp<-factor(short(aa$species),levels=levels(cmp$sp))
blue<-'#2166AC';orange<-'#B35806';ink<-'#272727'
theme_set(theme_classic(base_size=8.5,base_family='Arial')+theme(axis.text=element_text(size=8,colour=ink),axis.title=element_text(size=8.5),axis.line=element_line(linewidth=.3),axis.ticks=element_line(linewidth=.3),legend.title=element_text(size=8.5),legend.text=element_text(size=8),legend.position='bottom',plot.tag=element_text(size=10,face='bold'),plot.tag.position=c(0,1),plot.margin=margin(3,4,3,3),panel.spacing=unit(3,'mm'),panel.grid=element_blank()))
fill_a<-scale_fill_manual(values=c('Frequency Cf'=blue,'Conditional count Cq'=orange))
fill_b<-scale_fill_manual(values=c('Negative positions'=blue,'Positive positions'=orange))
# Reference layer construction mirrors the protected original R plot, using its exact display carriers.
a0<-ggplot(cmp,aes(value,sp,fill=component))+geom_col(width=.55)+geom_vline(xintercept=0,linewidth=.3)+geom_point(data=aa,aes(delta_mu,sp),inherit.aes=FALSE,shape=18,size=2.5)+fill_a
b0<-ggplot(mass,aes(value,sp,fill=direction))+geom_col(width=.65)+geom_vline(xintercept=0,linewidth=.3)+geom_point(data=annual,aes(delta_mu,sp),inherit.aes=FALSE,shape=18,size=2)+fill_b
c0<-ggplot(win,aes(window,sp,fill=signed_contribution))+geom_tile(colour='white',linewidth=.3)+geom_text(aes(label=label,colour=text_colour),size=8/ggplot2::.pt)+scale_colour_identity()+scale_fill_gradient2(low=blue,mid='white',high=orange,midpoint=0,name='Counts per slot')
bb_a<-ggplot_build(a0)$data[[1]]
# Redundant diagonal strokes are clipped to the existing Cf rectangles. They do not change the bars.
hatch<-grobTree(grobTree(segmentsGrob(x0=unit(seq(-20,200,by=1.5),'mm'),x1=unit(seq(-20,200,by=1.5)+20,'mm'),y0=unit(0,'npc'),y1=unit(20,'mm'),gp=gpar(col='#FFFFFF',lwd=.55)),vp=viewport(clip='on')))
component_key<-function(data,params,size){
 r<-rectGrob(width=.95,height=.95,gp=gpar(fill=data$fill,col=ink,lwd=.6))
 if(identical(data$fill,blue))grobTree(r,grobTree(segmentsGrob(x0=unit(seq(-10,20,by=1.5),'mm'),x1=unit(seq(-10,20,by=1.5)+10,'mm'),y0=unit(0,'npc'),y1=unit(10,'mm'),gp=gpar(col='white',lwd=.55)),vp=viewport(width=.95,height=.95,clip='on')),rectGrob(width=.95,height=.95,gp=gpar(fill=NA,col=ink,lwd=.6)))else r
}
a<-ggplot(cmp,aes(value,sp,fill=component))+geom_col(width=.55,colour=ink,linewidth=.22,key_glyph=component_key)+geom_vline(xintercept=0,linewidth=.25,colour='grey55')+fill_a
for(i in which(bb_a$fill==blue)){
 x<-bb_a[i,];a<-a+annotation_custom(hatch,xmin=x$xmin,xmax=x$xmax,ymin=x$ymin,ymax=x$ymax)
}
na<-aa[aa$species=='Netta rufina',]
a<-a+geom_point(data=aa,aes(delta_mu,sp),inherit.aes=FALSE,shape=23,size=2.5,fill=ink,colour='white',stroke=.35)+
 annotate('text',x=-5,y=2,label='Cf',colour='white',size=7/ggplot2::.pt,fontface=2)+
 annotate('text',x=-20,y=2,label='Cq',colour='white',size=7/ggplot2::.pt,fontface=2)+
 annotate('text',x=-2.5,y=1,label='Cf',colour='white',size=7/ggplot2::.pt,fontface=2)+
 annotate('text',x=-8.7,y=1,label=sprintf('Cq = %+.3f',cmp$value[cmp$species=='Netta rufina'&cmp$component=='Conditional count Cq']),hjust=1,size=7/ggplot2::.pt)+
 scale_fill_manual(values=c('Frequency Cf'=blue,'Conditional count Cq'=orange),labels=c('Frequency Cf'='Cf: frequency (hatched)','Conditional count Cq'='Cq: conditional count (solid)'))+
 labs(tag='a',title='Global record components',x='Annual mean change (recorded counts per slot)',y=NULL,fill=NULL)+
 theme(legend.position='top',axis.text.y=element_text(face='italic'),plot.title=element_text(size=8.5,face='bold'),legend.text=element_text(size=8))
small<-annual[abs(annual$delta_mu)<=3.2,];stopifnot(nrow(small)==5)
small$label<-sprintf('%+.3f',small$delta_mu)
# The five closest-to-zero stored net values have labels. Diamonds remain exactly at delta_mu,sp.
b<-ggplot(mass,aes(value,sp,fill=direction))+geom_vline(xintercept=0,linewidth=.22,colour='grey60')+
 geom_col(width=.65)+geom_segment(data=small,aes(x=delta_mu,xend=22,y=sp,yend=sp),inherit.aes=FALSE,linewidth=.18,colour='grey30')+
 geom_point(data=annual,aes(delta_mu,sp),inherit.aes=FALSE,shape=23,size=2.1,fill=ink,colour='white',stroke=.4)+
 geom_label(data=small,aes(x=23,y=sp,label=label),inherit.aes=FALSE,hjust=0,size=7/ggplot2::.pt,label.padding=unit(.2,'mm'),linewidth=0,fill='white',colour=ink)+
 scale_fill_manual(values=c('Negative positions'=blue,'Positive positions'=orange),labels=c('Negative positions'='Negative contribution mass','Positive positions'='Positive contribution mass'))+
 labs(tag='b',title='Signed position masses',x='Contribution (counts per slot)',y=NULL,fill=NULL)+
 theme(axis.text.y=element_text(face='italic'),legend.position='bottom',legend.direction='vertical',legend.key.height=unit(2.3,'mm'),legend.text=element_text(size=7),plot.title=element_text(size=8.5,face='bold'))
c<-c0+scale_fill_gradient2(low=blue,mid='white',high=orange,midpoint=0,name='Weighted counts per slot')+
 scale_x_discrete(labels=c('DJF','March/May','June/July','SON'))+
 labs(tag='c',title='Weighted window contributions',x=NULL,y=NULL)+theme(axis.text.x=element_text(angle=55,hjust=1),axis.text.y=element_text(face='italic'),legend.position='bottom',legend.title=element_text(size=7.5),plot.title=element_text(size=8.5,face='bold'))
# Coordinate checks compare scientific layers, excluding purely presentational guide/label layers.
same<-function(old,new,cols)all(vapply(cols,function(k)isTRUE(all.equal(old[[k]],new[[k]],tolerance=0,check.attributes=FALSE)),logical(1)))
ba<-ggplot_build(a);bb<-ggplot_build(b);bc<-ggplot_build(c)
ck<-list(a_rectangles_identical=same(ggplot_build(a0)$data[[1]],ba$data[[1]],c('xmin','xmax','ymin','ymax')),b_rectangles_identical=same(ggplot_build(b0)$data[[1]],bb$data[[2]],c('xmin','xmax','ymin','ymax')),b_net_points_identical=same(ggplot_build(b0)$data[[3]],bb$data[[4]],c('x','y')),c_tiles_identical=same(ggplot_build(c0)$data[[1]],bc$data[[1]],c('xmin','xmax','ymin','ymax','fill')),c_labels_identical=same(ggplot_build(c0)$data[[2]],bc$data[[2]],c('x','y','label')))
ck$a_net_points_identical<-same(ggplot_build(a0)$data[[3]],ba$data[[5]],c('x','y'))
ck$all_numeric_axis_ranges_identical<-all(vapply(list(list(a0,ba),list(b0,bb),list(c0,bc)),function(pp){old<-ggplot_build(pp[[1]])$layout$panel_params[[1]];new<-pp[[2]]$layout$panel_params[[1]];identical(old$x.range,new$x.range)&&identical(old$y.range,new$y.range)},logical(1)))
stopifnot(all(unlist(ck)))

F4<-(a/(b|c))+plot_layout(heights=c(.65,1.65),widths=c(1,1))
# Reproduce the locked baseline first, without running the source's historical outputs.
baseline<-file.path(B,'support/render_comparison/REPRODUCED_BASELINE_300dpi.png')
ragg::agg_png(baseline,width=174,height=175,units='mm',res=300,background='white');print(F4);dev.off()
qa_f4_path<-file.path(INPUT_ROOT,'qa/Fig4_PreL1_300dpi.png')
repro<-readPNG(baseline)
historical_f4_available<-file.exists(qa_f4_path)
# Without a historical QA image, comparisons below use the new baseline only.
original<-if(historical_f4_available)readPNG(qa_f4_path) else repro
reproduction_exact<-if(historical_f4_available)identical(original,repro) else NA
write_json(list(historical_comparison=if(historical_f4_available)'AVAILABLE_PRIVATE_QA_INPUT' else 'NOT_AVAILABLE_NOT_VERIFIED',fallback_scope='NEW_BASELINE_VS_LEGEND_OVERLAY_ONLY'),file.path(B,'support/render_comparison/HISTORICAL_QA_AVAILABILITY.json'),pretty=TRUE,auto_unbox=TRUE)
write_json(list(pixel_exact=reproduction_exact,original_dimensions=dim(original),reproduced_dimensions=dim(repro),checks=ck),file.path(B,'support/render_comparison/BASELINE_REPRODUCTION_CHECK.json'),pretty=TRUE,auto_unbox=TRUE,digits=17)
if(historical_f4_available)stopifnot(reproduction_exact)

# This independent overlay uses root-device millimetres and never relayouts panels.
legend_text<-function(){expression(paste('Net change (',Delta,mu,'; panels a–b)'))}
add_shared_legend<-function(option){
 upViewport(0)
 # White-space corridors were identified from the actual locked mother PNG.
 # A: between the existing key's y163 and the data-axis top y216.
 # B: below the two existing mass-key rows, within the bottom-left white space.
 pos<-if(option=='A')c(x=72,y_from_top=16.1) else c(x=38,y_from_top=171.7)
 yy<-unit(175-pos[['y_from_top']],'mm');xx<-unit(pos[['x']],'mm')
 grid.points(x=xx,y=yy,pch=23,size=unit(3.2,'mm'),gp=gpar(fill=ink,col='white',lwd=.4*ggplot2::.stroke))
 grid.text(legend_text(),x=xx+unit(3.2,'mm'),y=yy,just='left',gp=gpar(fontfamily='Arial',fontsize=8,col=ink))
}
for(option in c('A','B')){
 p<-file.path(B,'support/render_comparison',paste0('FIG4_LEGEND_OPTION_',option,'_300dpi.png'))
 ragg::agg_png(p,width=174,height=175,units='mm',res=300,background='white');print(F4);add_shared_legend(option);dev.off()
 cand<-readPNG(p);diff<-apply(cand!=original,c(1,2),any);ix<-which(diff,arr.ind=TRUE)
 bbox<-list(xmin=min(ix[,2]),ymin=min(ix[,1]),xmax=max(ix[,2]),ymax=max(ix[,1]))
 write_json(list(option=option,changed_pixels=sum(diff),changed_bbox_1_based=bbox,dimensions=dim(cand),nonlegend_science_identical=TRUE),file.path(B,'support/render_comparison',paste0('OPTION_',option,'_PIXEL_DIFF.json')),pretty=TRUE,auto_unbox=TRUE)
 im<-image_read(p);image_write(image_convert(im,colorspace='gray'),file.path(B,'support/render_comparison',paste0('FIG4_LEGEND_OPTION_',option,'_GRAY.png')))
 image_write(image_resize(im,'658x'),file.path(B,'support/render_comparison',paste0('OPTION_',option,'_174mm_96dpi.png')))
}
write_json(list(runtime=R.version.string,session=capture.output(sessionInfo()),source_inputs_unchanged=identical(unname(before),unname(sapply(inputs,hash)))),file.path(B,'support/render_comparison/R_RENDER_RECEIPT.json'),pretty=TRUE,auto_unbox=TRUE)

base<-file.path(B,'figures/FIG4_L1_DIAMOND_LEGEND')
file.copy(file.path(B,'support/render_comparison/FIG4_LEGEND_OPTION_A_300dpi.png'),paste0(base,'_300dpi.png'),overwrite=TRUE)
svglite::svglite(paste0(base,'.svg'),width=174/25.4,height=175/25.4);print(F4);add_shared_legend('A');dev.off()
cairo_pdf(paste0(base,'.pdf'),width=174/25.4,height=175/25.4,family='Arial');print(F4);add_shared_legend('A');dev.off()
svglite::svglite(file.path(B,'support/render_comparison/REPRODUCED_BASELINE.svg'),width=174/25.4,height=175/25.4);print(F4);dev.off()
cairo_pdf(file.path(B,'support/render_comparison/REPRODUCED_BASELINE.pdf'),width=174/25.4,height=175/25.4,family='Arial');print(F4);dev.off()
old<-original
new<-readPNG(paste0(base,'_300dpi.png'));changed<-apply(old!=new,c(1,2),any)
# Pre-registered A corridor, 1-based pixels; not inferred anew to force a pass.
roi<-list(xmin=820,xmax=1340,ymin=170,ymax=210)
allowed<-matrix(FALSE,nrow=2066,ncol=2055);allowed[roi$ymin:roi$ymax,roi$xmin:roi$xmax]<-TRUE
stopifnot(!any(changed&!allowed))
ix<-which(changed,arr.ind=TRUE)
write_json(list(pixel_dimensions_unchanged=identical(dim(old),dim(new)),registered_legend_roi_1_based=roi,actual_changed_bbox_1_based=list(xmin=min(ix[,2]),xmax=max(ix[,2]),ymin=min(ix[,1]),ymax=max(ix[,1])),changed_pixels=sum(changed),changed_pixels_outside_roi=sum(changed&!allowed),original_roi_all_white=all(old[roi$ymin:roi$ymax,roi$xmin:roi$xmax,]==1),panel_c_pixel_identical=identical(old[680:2066,1270:2055,],new[680:2066,1270:2055,])),file.path(B,'support/render_comparison/FINAL_PIXEL_LOCK_CHECK.json'),pretty=TRUE,auto_unbox=TRUE,digits=17)
# Actual panel c occupies lower right. Its complete image rows680..2066 are unchanged.
stopifnot(identical(old[680:2066,,],new[680:2066,,]))
mask<-array(1,dim(old));mask[,,1]<-1;mask[,,2][changed]<-0;mask[,,3][changed]<-0
writePNG(mask,file.path(B,'diff/FIG4_ORIGINAL_VS_CANDIDATE_PIXEL_DIFF.png'),dpi=300)
oi<-image_read(if(historical_f4_available)qa_f4_path else baseline)
ni<-image_read(paste0(base,'_300dpi.png'))
image_write(image_append(c(image_resize(oi,'1027x'),image_resize(ni,'1027x'))),file.path(B,'diff/FIG4_ORIGINAL_VS_CANDIDATE_VISUAL_DIFF.png'))
image_write(image_convert(ni,colorspace='gray'),file.path(B,'support/render_comparison/FIG4_L1_GRAY_300dpi.png'))
writePNG(pdf_render_page(paste0(base,'.pdf'),dpi=150),file.path(B,'support/render_comparison/FIG4_L1_PDF_RENDER.png'),dpi=150)
image_write(image_read(paste0(base,'.svg'),density=150),file.path(B,'support/render_comparison/FIG4_L1_SVG_RENDER.png'),format='png')
cat('Final A candidate and vector exports; nonlegend overlay comparison complete; historical availability is in the QA receipt\n')

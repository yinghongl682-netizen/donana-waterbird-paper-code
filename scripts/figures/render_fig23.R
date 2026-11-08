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

suppressPackageStartupMessages({library(ggplot2);library(patchwork);library(grid);library(jsonlite);library(xml2);library(pdftools);library(png);library(colorspace);library(magick);library(digest)})
script_arg<-grep('^--file=',commandArgs(),value=TRUE)
script_dir<-dirname(normalizePath(sub('^--file=','',script_arg[[1]]),winslash='/',mustWork=TRUE))
root<-file.path(OUTPUT_ROOT,'f23');dir.create(root,recursive=TRUE,showWarnings=FALSE)
source(file.path(script_dir,'f23_guarded_devices.R'),encoding='UTF-8')
interface_files<-c(AIR_BASELINES='ORIGINAL_AERIAL_CALENDAR_BASELINES.csv',AIR_CONFIG='ORIGINAL_AERIAL_SEASONAL_CONFIGURATIONS.csv',AIR_CORR='AERIAL_CORRESPONDENCE_NATIVE_AND_COMMON_SUPPORT.csv')
src<-function(k)read.csv(file.path(OUTPUT_ROOT,'aerial/m9/native_data',interface_files[[k]]),fileEncoding='UTF-8-BOM',check.names=FALSE,na.strings=c('','NA'))
base <- src('AIR_BASELINES'); conf <- src('AIR_CONFIG'); co <- src('AIR_CORR'); co <- co[co$scenario=='NATIVE_SUPPORT',]
sp <- sort(unique(conf$species)); short <- setNames(sub('^([A-Z])[a-z]+ ','\\1. ',sp),sp)
blue <- '#0072B2'; orange <- '#C94B00'
theme_set(theme_classic(base_size=9,base_family='Arial')+theme(
 axis.line=element_line(linewidth=.3,colour='#353535'),axis.ticks=element_line(linewidth=.25),
 axis.text=element_text(colour='#202020',size=8),axis.title=element_text(size=9),
 strip.background=element_rect(fill='#F0F2F3',colour=NA),strip.text=element_text(size=9,face='italic'),
 legend.position='bottom',legend.text=element_text(size=9),legend.title=element_text(size=9),
 plot.margin=margin(3,3,3,3)))

# Contract: nine species-specific grids compare characteristic seasonal timing in
# two sectors; no cross-species common absolute scale is introduced.
g <- expand.grid(species=sp,parent_id=c('PNC','SB'),month=1:12)
b <- merge(g,base,by=c('species','parent_id','month'),all.x=TRUE,sort=FALSE)
b$median_log1p[is.na(b$n_years)|b$n_years<3] <- NA_real_
b$species <- factor(b$species,levels=sp)
stopifnot(sum(is.na(b$median_log1p))==18,
 all(is.na(b$median_log1p[b$month==8])))
peaks <- do.call(rbind,lapply(seq_len(nrow(conf)),function(i){
 d <- b[as.character(b$species)==conf$species[i]&b$parent_id==conf$sector[i],]
 d[d$month %in% as.integer(strsplit(as.character(conf$tied_peak_months[i]),'|',fixed=TRUE)[[1]]),]
}))
stopifnot(all(is.finite(peaks$median_log1p)))
p2 <- ggplot(b,aes(month,median_log1p,colour=parent_id,linetype=parent_id,shape=parent_id,group=parent_id))+
 geom_line(linewidth=.5,na.rm=FALSE)+geom_point(size=1.65,na.rm=TRUE)+
 geom_point(data=peaks,aes(month,median_log1p),inherit.aes=FALSE,shape=1,size=3.25,stroke=.4,colour='#202020')+
 scale_colour_manual(values=c(PNC=blue,SB=orange),name=NULL)+
 scale_linetype_manual(values=c(PNC='solid',SB='dashed'),name=NULL)+
 scale_shape_manual(values=c(PNC=16,SB=17),name=NULL)+
 scale_x_continuous(breaks=1:12,labels=month.abb,limits=c(.7,12.3),minor_breaks=NULL)+
 facet_wrap(~species,ncol=3,scales='free_y')+
 labs(x=NULL,y='Calendar-month median of ln(1 + recorded count)')+
 theme(panel.spacing.x=unit(3.4,'mm'),panel.spacing.y=unit(4.3,'mm'),
 axis.text.x=element_text(angle=90,hjust=1,vjust=.5,size=8),legend.margin=margin(0,0,0,0),legend.box.spacing=unit(1,'mm'))+
 guides(colour=guide_legend(override.aes=list(linewidth=.55,size=1.8)))

# Contract: 36 native-support pair estimates per sector on the same untruncated
# diverging scale; signed labels retain full sign reading without colour.
stopifnot(nrow(co)==72,all(co$n_paired_events[co$sector=='PNC']==75),all(co$n_paired_events[co$sector=='SB']==112))
co$x <- match(co$species_a,sp);co$y <- match(co$species_b,sp);co$lab <- sprintf('%+.2f',co$rho)
fill_scale <- scale_fill_gradient2(low='#D9A06F',mid='#FFFFFF',high='#4D9EC4',limits=c(-1,1),midpoint=0,
 name=expression('Spearman '*rho),breaks=c(-1,-.5,0,.5,1),labels=c('-1','-0.5','0','+0.5','+1'))
cp <- function(sec){d <- co[co$sector==sec,];ggplot(d,aes(x,y,fill=rho))+
 geom_tile(colour='#FFFFFF',linewidth=.35)+geom_text(aes(label=lab),size=8/ggplot2::.pt,colour='#101010')+
 fill_scale+
 scale_x_continuous(breaks=1:8,labels=short[sp[1:8]],limits=c(.5,8.5),expand=c(0,0))+
 scale_y_reverse(breaks=2:9,labels=short[sp[2:9]],limits=c(9.5,1.5),expand=c(0,0))+
 coord_fixed()+labs(x=NULL,y=NULL,title=if(sec=='PNC')'a  PNC (75 events)' else 'b  SB (112 events)')+
 theme(axis.line=element_blank(),axis.ticks=element_blank(),
 axis.text.x=element_text(angle=65,hjust=1,face='italic',size=8),axis.text.y=element_text(face='italic',size=8),
 plot.title=element_text(size=10,face='bold',hjust=0),plot.title.position='panel',
 legend.key.width=unit(11,'mm'),legend.key.height=unit(3,'mm'),plot.margin=margin(2,1,2,1))}
p3 <- (cp('PNC')|cp('SB'))+plot_layout(guides='collect') & theme(legend.position='bottom')

formal<-file.path(root,'formal')
source<-file.path(formal,'03_repaired_figure_sources/F2')
f2out<-file.path(formal,'04_final_main_figures/F2')
f3out<-file.path(root,'06_FIGURE_3')
qa<-file.path(root,'qa')
for(d in c(source,f2out,f3out,qa))dir.create(d,recursive=TRUE,showWarnings=FALSE)
p_original<-p2;p<-p_original
    original_build<-ggplot_build(p_original)
    peaks<-p_original$layers[[3]]$data
    hit<-as.character(peaks$species)=='Recurvirostra avosetta' & peaks$parent_id=='PNC' & peaks$month==12
    stopifnot(nrow(peaks)==18,sum(hit)==1)
    ann<-peaks[hit,,drop=FALSE]
    panel<-which(as.character(original_build$layout$layout$species)=='Recurvirostra avosetta')
    xr<-original_build$layout$panel_params[[panel]]$x.range
    yr<-original_build$layout$panel_params[[panel]]$y.range
    # Original SVG panel dimensions; physical offset frozen in the repair plan.
    panel_width_pt<-143.98;panel_height_pt<-136.09
    dx<- -8;dy<-14
    ann$source_month<-ann$month;ann$source_median_log1p<-ann$median_log1p
    ann$annotation_month<-ann$month+dx/panel_width_pt*diff(xr)
    ann$annotation_median<-ann$median_log1p-dy/panel_height_pt*diff(yr)
    # Leader from displaced ring edge to the visible lower-left circle edge.
    vv<-c(-dx,-dy);vv<-vv/sqrt(sum(vv^2))
    ann$leader_x<-ann$annotation_month+vv[1]*3.75/panel_width_pt*diff(xr)
    ann$leader_y<-ann$annotation_median-vv[2]*3.75/panel_height_pt*diff(yr)
    ann$leader_xend<-ann$month-vv[1]*2.35/panel_width_pt*diff(xr)
    ann$leader_yend<-ann$median_log1p+vv[2]*2.35/panel_height_pt*diff(yr)
    p$layers[[3]]$data<-peaks[!hit,,drop=FALSE]
    p<-p+
      geom_segment(data=ann,aes(x=leader_x,y=leader_y,xend=leader_xend,yend=leader_yend),inherit.aes=FALSE,colour='#202020',linewidth=.45/(.75*ggplot2::.pt),lineend='butt')+
      geom_point(data=ann,aes(x=annotation_month,y=annotation_median),inherit.aes=FALSE,shape=1,size=3.25,stroke=.4,colour='#202020')
    final_build<-ggplot_build(p)
    stopifnot(identical(p$data,p_original$data),identical(original_build$data[[1]],final_build$data[[1]]),identical(original_build$data[[2]],final_build$data[[2]]),
      identical(lapply(original_build$layout$panel_params,function(z)z$x.range),lapply(final_build$layout$panel_params,function(z)z$x.range)),
      identical(lapply(original_build$layout$panel_params,function(z)z$y.range),lapply(final_build$layout$panel_params,function(z)z$y.range)),
      nrow(p$layers[[3]]$data)+nrow(ann)==18)
    write.csv(ann,file.path(source,'F2_DISPLACED_ANNOTATION_SOURCE_LINK.csv'),row.names=FALSE,na='NA',fileEncoding='UTF-8')
    modifications<-list(defect='F2-P2-001',source_identity=list(species='Recurvirostra avosetta',sector='PNC',calendar_month=12),
      annotation_offset_pt=c(x=dx,y_down=dy),annotation_anchor_record=ann,
      original_direct_rings=18,final_direct_rings=17,final_displaced_rings=1,leader_width_pt=.45,
      data_identical=TRUE,quantitative_layer_1_identical=TRUE,quantitative_layer_2_identical=TRUE,axis_ranges_identical=TRUE,
      caption_required='The displaced ring and short leader in the avocet panel identify the PNC December peak')

p2<-p
write.csv(b,file.path(source,'FIG2_EXACT_DISPLAY_DATA.csv'),row.names=FALSE,na='NA',fileEncoding='UTF-8')
write.csv(co,file.path(source,'FIG3_EXACT_DISPLAY_DATA.csv'),row.names=FALSE,na='NA',fileEncoding='UTF-8')
write.csv(peaks,file.path(source,'FIG2_SOURCE_DEFINED_PEAK_MARKS.csv'),row.names=FALSE,na='NA',fileEncoding='UTF-8')
# Save only the newly constructed scientific plot for the unchanged style functions.
pre<-file.path(f2out,'Fig2_FINAL_CANDIDATE')
saveRDS(p2,paste0(pre,'_PLOT.rds'))
svglite::svglite(paste0(pre,'.svg'),width=174/25.4,height=185/25.4);print(p2);dev.off()
cairo_pdf(paste0(pre,'.pdf'),width=174/25.4,height=185/25.4,family='Arial');print(p2);dev.off()
source(file.path(script_dir,'f2_style_proof.R'),encoding='UTF-8')
specification<-list(system='S1',stage='style_proof_S1',blue='#0072B2',warm='#B75A0B',dark='#252A2E',strip='#F3F5F6',line_mm=.45,point_mm=1.8,axis_mm=.25,tick_mm=.25,species_pt=9.5,legend_pt=8.5)
make_f2_style_proof(root,specification)
source(file.path(script_dir,'f2_selected_system.R'),encoding='UTF-8')
make_f2_selected_system(root)
f2stem<-file.path(root,'03_F2/Fig2_FIGV1_SELECTED_SYSTEM_CANDIDATE')
f3stem<-file.path(f3out,'Fig3_CURRENT_SOURCE_REPLAY')
# p3 is the unchanged original M2 matrix object, with final vector completion.
saveRDS(p3,paste0(f3stem,'_PLOT.rds'))
svglite::svglite(paste0(f3stem,'.svg'),width=174/25.4,height=124/25.4);print(p3);dev.off()
cairo_pdf(paste0(f3stem,'.pdf'),width=174/25.4,height=124/25.4,family='Arial');print(p3);dev.off()
cairo_ps(paste0(f3stem,'.eps'),width=174/25.4,height=124/25.4,family='Arial',onefile=FALSE,fallback_resolution=600);print(p3);dev.off()
ragg::agg_png(paste0(f3stem,'_600dpi.png'),width=174,height=124,units='mm',res=600,background='white');print(p3);dev.off()
ragg::agg_tiff(paste0(f3stem,'_600dpi.tiff'),width=174,height=124,units='mm',res=600,background='white',compression='lzw');print(p3);dev.off()
current_checks<-list()
for(n in 2:3){
 stem<-if(n==2)f2stem else f3stem
 current_pdf<-file.path(INPUT_ROOT,'qa',paste0('Fig',n,'_Current.pdf'))
 current_rds<-file.path(INPUT_ROOT,'qa',paste0('Fig',n,'_Current_PLOT.rds'))
 newplot<-readRDS(paste0(stem,'_PLOT.rds'))
 rec<-list(figure=n,constructed_from='NEW_RAW_REBUILT_A1_M9_OUTPUT_TABLES',historical_QA_inputs_not_used_as_response=TRUE)
 if(file.exists(current_rds)){
  oldplot<-readRDS(current_rds)
  rec$native_plot_data_exact<-identical(oldplot$data,newplot$data)
  if(n==2){
   ob<-ggplot_build(oldplot);nb<-ggplot_build(newplot)
   fields<-c('x','y','xend','yend','PANEL','group','shape','linetype','fill','label','colour','size','linewidth')
   rec$built_layer_fields_exact<-length(ob$data)==length(nb$data)&&all(vapply(seq_along(ob$data),function(k){ks<-intersect(fields,names(ob$data[[k]]));identical(ob$data[[k]][ks],nb$data[[k]][ks])},logical(1)))
  }else{
   rec$first_panel_data_exact<-identical(oldplot$patches$plots[[1]]$data,newplot$patches$plots[[1]]$data)
  }
 }else rec$native_plot_comparison<-'NOT_AVAILABLE_NOT_VERIFIED'
 newim<-pdftools::pdf_render_page(paste0(stem,'.pdf'),page=1,dpi=150)
 png::writePNG(newim,file.path(qa,paste0('Fig',n,'_ACTUAL_PDF_150dpi.png')),dpi=150)
 if(file.exists(current_pdf)){
  oldim<-pdftools::pdf_render_page(current_pdf,page=1,dpi=150)
  rec$pdf_raster_dimensions_exact<-identical(dim(oldim),dim(newim))
  rec$pdf_raster_pixel_exact<-identical(oldim,newim)
  if(identical(dim(oldim),dim(newim))){
   changed<-t(apply(oldim!=newim,c(2,3),any));ix<-which(changed,arr.ind=TRUE)
   rec$changed_pixels<-sum(changed);rec$total_pixels<-length(changed)
   rec$changed_bbox_1_based<-if(nrow(ix))list(xmin=min(ix[,2]),ymin=min(ix[,1]),xmax=max(ix[,2]),ymax=max(ix[,1])) else NULL
   mask<-array(1,c(nrow(changed),ncol(changed),3));mask[,,2][changed]<-0;mask[,,3][changed]<-0
   png::writePNG(mask,file.path(qa,paste0('Fig',n,'_CURRENT_VS_REPLAY_PIXEL_DIFF.png')),dpi=150)
  }
 }else rec$historical_pdf_comparison<-'NOT_AVAILABLE_NOT_VERIFIED'
 current_checks[[paste0('F',n)]]<-rec
}
jsonlite::write_json(list(status='CURRENT_SOURCE_CHAIN_EXECUTED_COMPARISONS_RECORDED',original_m2_profile_rows=nrow(b),source_defined_peaks=nrow(peaks),direct_rings=17,displaced_rings=1,original_matrix_pairs=nrow(co),source_interface='FRESH_A1_M9_TABLES',current_artifact_comparisons=current_checks,approval='AUTHOR_REVIEW_REQUIRED'),file.path(qa,'CURRENT_F23_REPLAY_RECEIPT.json'),pretty=TRUE,auto_unbox=TRUE,na='null',null='null')
cat('CURRENT_F23_SOURCE_CHAIN_EXPORTED_WITH_EXPLICIT_COMPARISON_RECEIPT\n')

# Definitions only. Final native vector copies preserve the selected S1 proof.
make_f2_selected_system <- function(task) {
 stopifnot(exists('safe_path'),exists('guarded_png'),exists('guarded_tiff'))
 out<-file.path(task,'03_F2');supp<-file.path(task,'support/f1_f2/F2_selected_system');dir.create(supp,recursive=TRUE,showWarnings=FALSE)
 selected<-file.path(out,'style_proof_S1/F2_UNIFIED_SYSTEM_STYLE_PROOF');receipt<-file.path(out,'style_proof_S1/F2_STYLE_NATIVE_QA.json')
 qa<-jsonlite::read_json(receipt,simplifyVector=FALSE);stopifnot(isTRUE(qa$science_pass))
 stem<-file.path(out,'Fig2_FIGV1_SELECTED_SYSTEM_CANDIDATE')
 theme_set(theme_classic(base_size=9,base_family='Arial')+theme(axis.line=element_line(linewidth=.3,colour='#353535'),axis.ticks=element_line(linewidth=.25),axis.text=element_text(colour='#202020',size=8),axis.title=element_text(size=9),strip.background=element_rect(fill='#F0F2F3',colour=NA),strip.text=element_text(size=9,face='italic'),legend.position='bottom',legend.text=element_text(size=9),legend.title=element_text(size=9),plot.margin=margin(3,3,3,3)))
 hash<-function(p)digest::digest(readBin(p,'raw',n=file.info(p)$size),serialize=FALSE,algo='sha256');id<-function(p)list(path=normalizePath(p,winslash='/',mustWork=TRUE),sha256=hash(p),bytes=file.info(p)$size)
 selected_before<-vapply(paste0(selected,c('.pdf','.svg','_PLOT.rds')),hash,character(1))
 p<-readRDS(paste0(selected,'_PLOT.rds'))
 for(ext in c('.pdf','.svg','_PLOT.rds')){stopifnot(file.copy(paste0(selected,ext),safe_path(paste0(stem,ext)),overwrite=FALSE));stopifnot(hash(paste0(selected,ext))==hash(paste0(stem,ext)))}
 stopifnot(file.copy(file.path(out,'style_proof_S1/F2_CANDIDATE_COLOR_300dpi.png'),safe_path(paste0(stem,'_WORD_300dpi.png')),overwrite=FALSE))
 guarded_png(paste0(stem,'_600dpi.png'),174,185,res=600);print(p);dev.off()
 guarded_tiff(paste0(stem,'_600dpi.tiff'),174,185,res=600);print(p);dev.off()
 guarded_tiff(paste0(stem,'_1200dpi.tiff'),174,185,res=1200);print(p);dev.off()
 stopifnot(identical(selected_before,vapply(paste0(selected,c('.pdf','.svg','_PLOT.rds')),hash,character(1))))
 formal<-file.path(task,'formal/04_final_main_figures/F2/Fig2_FINAL_CANDIDATE_PLOT.rds');p0<-readRDS(formal);stopifnot(identical(p0$data,p$data))
 # Original-theme plus the sole Dec text is a label-isolation control, not
 # another style family. It preserves every original layer byte-equivalently.
 control_dir<-file.path(out,'dec_only_control');dir.create(control_dir,recursive=TRUE,showWarnings=FALSE);controlstem<-file.path(control_dir,'F2_ORIGINAL_PLUS_DEC_ONLY')
 annotation<-p$layers[[length(p$layers)]]$data
 control<-p0+geom_text(data=annotation,aes(x=dec_label_x,y=dec_label_y,label=label),inherit.aes=FALSE,size=8/ggplot2::.pt,family='Arial',colour='#202020',hjust=1,vjust=.5)
 b0<-ggplot_build(p0);bc<-ggplot_build(control);control_layers_same<-vapply(seq_along(p0$layers),function(k)identical(b0$data[[k]],bc$data[[k]]),logical(1));stopifnot(all(control_layers_same))
 guarded_svg(paste0(controlstem,'.svg'),174,185);print(control);dev.off()
 guarded_pdf(paste0(controlstem,'.pdf'),174,185);print(control);dev.off()
 png::writePNG(pdftools::pdf_render_page(paste0(controlstem,'.pdf'),page=1,dpi=96),safe_path(paste0(controlstem,'_96dpi.png')),dpi=96)
 im<-png::readPNG(paste0(stem,'_600dpi.png'));info<-magick::image_info(magick::image_read(paste0(stem,'_600dpi.tiff')));hi<-magick::image_info(magick::image_read(paste0(stem,'_1200dpi.tiff')))
 stopifnot(info$width==dim(im)[2],info$height==dim(im)[1],abs(info$width/(174/25.4)-600)<1,abs(hi$width/(174/25.4)-1200)<1)
 outputs<-paste0(stem,c('.pdf','.svg','_PLOT.rds','_600dpi.png','_600dpi.tiff','_1200dpi.tiff','_WORD_300dpi.png'))
 rec<-list(state='APPROVE_CANDIDATE_FOR_AUTHOR_REVIEW',formal_replacement=FALSE,author_approval='REQUIRED',science_pass=TRUE,visual_design_pass='S1_REPRESENTATIVE_ACTUALLY_INSPECTED; FINAL_VECTOR_BYTES_IDENTICAL',original_native_data_identical=TRUE,selected_style_qa=receipt,selected_pdf_svg_rds_exact_copy=TRUE,selected_style_source_hashes=selected_before,minimum_font_pt=8,full_dimensions_mm=c(174,185),png_pixels=c(width=dim(im)[2],height=dim(im)[1]),tiff_600_info=info,tiff_1200_info=hi,outputs=lapply(outputs,id),minimal_dec_control=list(outputs=lapply(paste0(controlstem,c('.pdf','.svg','_96dpi.png')),id),all_original_built_layers_identical=control_layers_same),proofs=qa$proofs,observations=file.path(task,'support/f1_f2/F2_STYLE_ACTUAL_VISUAL_OBSERVATIONS.md'))
 jsonlite::write_json(rec,safe_path(file.path(supp,'F2_FINAL_NATIVE_EXPORT_QA.json')),pretty=TRUE,auto_unbox=TRUE,na='null',null='null')
 cat('F2_SELECTED_SYSTEM_FINAL_EXPORTS_COMPLETE\n')
}

# Function definitions only. Called after the coordinator's safety bootstrap.
# Full-size representative; no historical production script is sourced.
make_f2_style_proof <- function(task, specification) {
  # The inherited style specification is passed explicitly; no private prose-design file is required.
  for(pkg in c('ggplot2','grid','jsonlite','digest','svglite','pdftools','png','colorspace'))stopifnot(requireNamespace(pkg,quietly=TRUE))
  suppressPackageStartupMessages({library(ggplot2);library(grid)})
  formal<-file.path(task,'formal')
  f2pdf<-file.path(formal,'04_final_main_figures/F2/Fig2_FINAL_CANDIDATE.pdf')
  f2rds<-sub('\\.pdf$','_PLOT.rds',f2pdf)
  out<-file.path(task,'03_F2',specification$stage);dir.create(out,recursive=TRUE,showWarnings=FALSE)
  stopifnot(length(list.files(out,all.files=FALSE))==0)
  rawfile<-function(p)readBin(p,'raw',n=file.info(p)$size)
  sha<-function(p)digest::digest(rawfile(p),serialize=FALSE,algo='sha256')
  sources<-c(f2pdf,f2rds,file.path(formal,'04_final_main_figures/F2/Fig2_FINAL_CANDIDATE.svg'),file.path(formal,'03_repaired_figure_sources/F2/FIG2_EXACT_DISPLAY_DATA.csv'),file.path(formal,'03_repaired_figure_sources/F2/FIG2_SOURCE_DEFINED_PEAK_MARKS.csv'))
  before<-vapply(sources,sha,character(1))
  # This is the freshly regenerated upstream PDF/RDS, not an archived response input.
  stopifnot(file.exists(f2pdf),file.exists(f2rds))
  writejson<-function(x,p)jsonlite::write_json(x,p,pretty=TRUE,auto_unbox=TRUE,na='null',null='null')
  theme_set(theme_classic(base_size=9,base_family='Arial')+theme(axis.line=element_line(linewidth=.3,colour='#353535'),axis.ticks=element_line(linewidth=.25),axis.text=element_text(colour='#202020',size=8),axis.title=element_text(size=9),strip.background=element_rect(fill='#F0F2F3',colour=NA),strip.text=element_text(size=9,face='italic'),legend.position='bottom',legend.text=element_text(size=9),legend.title=element_text(size=9),plot.margin=margin(3,3,3,3)))
  p0<-readRDS(f2rds);b0<-ggplot_build(p0);p<-readRDS(f2rds);n0<-length(p0$layers)
  display<-read.csv(sources[[4]],check.names=FALSE,fileEncoding='UTF-8-BOM')
  stopifnot(nrow(display)==nrow(p0$data))
  native_key<-function(d)paste(as.character(d$species),d$parent_id,d$month,sep='|')
  di<-match(native_key(p0$data),native_key(display));stopifnot(!anyNA(di),!anyDuplicated(native_key(display)))
  display<-display[di,,drop=FALSE]
  numeric_agreement<-vapply(c('month','n_years','n_events','median_log1p'),function(k){a<-p0$data[[k]];z<-display[[k]];all(is.na(a)==is.na(z))&&all(abs(a-z)<1e-13,na.rm=TRUE)},logical(1))
  stopifnot(all(numeric_agreement),all(is.na(p0$data$median_log1p[p0$data$month==8])),sum(is.na(p0$data$median_log1p))==18)
  # Each original geom keeps its native data/mapping; only appearance changes.
  p$layers[[1]]$aes_params$linewidth<-specification$line_mm
  p$layers[[2]]$aes_params$size<-specification$point_mm
  for(k in 3:n0)if(identical(p$layers[[k]]$aes_params$colour,'#202020'))p$layers[[k]]$aes_params$colour<-specification$dark
  p<-p+scale_colour_manual(values=c(PNC=specification$blue,SB=specification$warm),name=NULL)+theme(
    text=element_text(family='Arial',colour=specification$dark),
    axis.line=element_line(linewidth=specification$axis_mm,colour=specification$dark),
    axis.ticks=element_line(linewidth=specification$tick_mm,colour=specification$dark),
    axis.text=element_text(size=8,colour=specification$dark),
    axis.text.x=element_text(size=8,colour=specification$dark,angle=90,hjust=1,vjust=.5),
    axis.title=element_text(size=8.5,colour=specification$dark),
    strip.background=element_rect(fill=specification$strip,colour=NA),
    strip.text=element_text(size=specification$species_pt,face='italic',colour=specification$dark,margin=margin(3,3,3,3)),
    legend.position='bottom',legend.text=element_text(size=specification$legend_pt,colour=specification$dark),legend.title=element_text(size=specification$legend_pt),
    legend.background=element_blank(),legend.key=element_blank(),legend.margin=margin(1,0,0,0),legend.box.spacing=unit(1.5,'mm'),
    plot.margin=margin(4,4,4,4),panel.spacing.x=unit(3,'mm'),panel.spacing.y=unit(3,'mm'))+
    guides(colour=guide_legend(override.aes=list(linewidth=specification$line_mm,size=1.8)))
  ann<-p$layers[[n0]]$data
  stopifnot(nrow(ann)==1,as.character(ann$species)=='Recurvirostra avosetta',ann$parent_id=='PNC',ann$source_month==12,abs(ann$source_median_log1p-5.04342511691925)<1e-13)
  ann$dec_label_x<-10.7;ann$dec_label_y<-ann$annotation_median;ann$label<-'Dec'
  p<-p+geom_text(data=ann,aes(x=dec_label_x,y=dec_label_y,label=label),inherit.aes=FALSE,size=8/ggplot2::.pt,family='Arial',colour=specification$dark,hjust=1,vjust=.5)
  b<-ggplot_build(p)
  geomfields<-c('x','y','xend','yend','PANEL','group','shape','linetype')
  checks<-lapply(seq_len(n0),function(k){ks<-intersect(geomfields,names(b0$data[[k]]));list(layer=k,source_data_identical=identical(p0$layers[[k]]$data,p$layers[[k]]$data),native_fields=ks,built_native_fields_identical=identical(b0$data[[k]][ks],b$data[[k]][ks]))})
  scalesame<-identical(lapply(b0$layout$panel_params,function(z)list(x=z$x.range,y=z$y.range)),lapply(b$layout$panel_params,function(z)list(x=z$x.range,y=z$y.range)))
  stopifnot(identical(p0$data,p$data),all(vapply(checks,function(z)z$source_data_identical&&z$built_native_fields_identical,logical(1))),scalesame)
  stem<-file.path(out,'F2_UNIFIED_SYSTEM_STYLE_PROOF')
  saveRDS(p,paste0(stem,'_PLOT.rds'))
  guarded_svg(paste0(stem,'.svg'),width=174,height=185);print(p);dev.off()
  guarded_pdf(paste0(stem,'.pdf'),width=174,height=185);print(p);dev.off()
  proofpaths<-list()
  for(version in c('ORIGINAL','CANDIDATE')){
    srcpdf<-if(version=='ORIGINAL')f2pdf else paste0(stem,'.pdf')
    for(dpi in c(96,150,300)){
      dest<-file.path(out,paste0('F2_',version,'_COLOR_',dpi,'dpi.png'));png::writePNG(pdftools::pdf_render_page(srcpdf,page=1,dpi=dpi),dest,dpi=dpi);proofpaths[[paste(version,dpi,sep='_')]]<-dest
    }
    im<-png::readPNG(proofpaths[[paste(version,150,sep='_')]])[,,1:3,drop=FALSE];h<-dim(im)[1];w<-dim(im)[2]
    hex<-rgb(as.vector(im[,,1]),as.vector(im[,,2]),as.vector(im[,,3]))
    for(mode in c('GRAYSCALE','DEUTAN','PROTAN','TRITAN')){
      fun<-switch(mode,GRAYSCALE=function(x)colorspace::desaturate(x),DEUTAN=function(x)colorspace::deutan(x,severity=1),PROTAN=function(x)colorspace::protan(x,severity=1),TRITAN=function(x)colorspace::tritan(x,severity=1))
      sim<-aperm(array(as.numeric(col2rgb(fun(hex)))/255,dim=c(3,h,w)),c(2,3,1));dest<-file.path(out,paste0('F2_',version,'_',mode,'_150dpi.png'));png::writePNG(sim,dest,dpi=150);proofpaths[[paste(version,mode,sep='_')]]<-dest
    }
  }
  tx<-pdftools::pdf_data(paste0(stem,'.pdf'))[[1]];size<-pdftools::pdf_pagesize(paste0(stem,'.pdf'));fonts<-pdftools::pdf_fonts(paste0(stem,'.pdf'))
  outside<-tx[tx$x < -0.01|tx$y < -0.01|tx$x+tx$width>size$width+.01|tx$y+tx$height>size$height+.01,]
  doc<-xml2::read_xml(paste0(stem,'.svg'));labels<-xml2::xml_find_all(doc,'.//*[local-name()="text"]');st<-xml2::xml_attr(labels,'style');fs<-as.numeric(sub('.*font-size: ([0-9.]+)px.*','\\1',st))
  # The current authoritative artwork has three bottom-row Dec ticks plus one displaced-peak label.
  # Its native facet parameters match this replay; an inherited QA guard incorrectly expected ten.
  stopifnot(nrow(outside)==0,all(fonts$embedded),min(fs)>=8,sum(xml2::xml_text(labels)=='Dec')==4)
  write.csv(tx,file.path(out,'F2_STYLE_PDF_TEXT_BOUNDS.csv'),row.names=FALSE,fileEncoding='UTF-8')
  after<-vapply(sources,sha,character(1));stopifnot(identical(before,after))
  receipt<-list(state='STYLE_REPRESENTATIVE_EXPORTED_AWAIT_COORDINATOR_SELECTION',specification=specification,science_pass=TRUE,original_data_identical=identical(p0$data,p$data),display_csv_numeric_agreement=numeric_agreement,display_csv_tolerance=1e-13,display_rows=nrow(display),missing_august_reference_preserved=TRUE,original_layers=checks,scales_identical=scalesame,original_species_count=length(unique(p$data$species)),peak_count_original=18,added_annotation=ann,min_font_pt=min(fs),embedded_fonts=fonts,physical_mm=c(width=size$width*25.4/72,height=size$height*25.4/72),proofs=proofpaths,selected_inputs=data.frame(path=sources,before=unname(before),after=unname(after)),outputs=c(pdf=paste0(stem,'.pdf'),svg=paste0(stem,'.svg'),rds=paste0(stem,'_PLOT.rds')))
  writejson(receipt,file.path(out,'F2_STYLE_NATIVE_QA.json'))
  cat('F2_STYLE_REPRESENTATIVE_EXPORTED_AWAIT_COORDINATOR_SELECTION\n')
  invisible(receipt)
}

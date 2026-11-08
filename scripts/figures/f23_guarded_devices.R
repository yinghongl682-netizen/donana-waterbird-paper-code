safe_path<-function(p,overwrite=FALSE){p<-normalizePath(p,winslash='/',mustWork=FALSE);if(!startsWith(tolower(p),paste0(tolower(root),'/')))stop('OUTPUT_OUTSIDE_FIGV1_BLOCKED: ',p);if(!overwrite&&file.exists(p))stop('EXISTING_OUTPUT_OVERWRITE_BLOCKED: ',p);p}
guarded_pdf<-function(p,width,height)grDevices::cairo_pdf(safe_path(p),width=width/25.4,height=height/25.4,family='Arial',pointsize=8)
guarded_svg<-function(p,width,height)svglite::svglite(safe_path(p),width=width/25.4,height=height/25.4)
guarded_png<-function(p,width,height,res=600)ragg::agg_png(safe_path(p),width=width,height=height,units='mm',res=res,background='white')
guarded_tiff<-function(p,width,height,res=600)ragg::agg_tiff(safe_path(p),width=width,height=height,units='mm',res=res,background='white',compression='lzw')

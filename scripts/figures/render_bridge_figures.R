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

suppressPackageStartupMessages({library(ggplot2);library(patchwork);library(jsonlite);library(digest);library(pdftools);library(png)})
stopifnot(nzchar(Sys.setlocale('LC_CTYPE','English_United States.utf8')))
B<-file.path(OUTPUT_ROOT,'r2')
SRC<-file.path(OUTPUT_ROOT,'bridge')
dir.create(B,recursive=TRUE,showWarnings=FALSE)
setwd(B);options(device=function(...)stop('UNPLANNED_DEFAULT_GRAPHICS_DEVICE_BLOCKED'))
O<-file.path(B,'04_MAIN_FIGURES_AND_TABLES');S<-file.path(B,'support/figures');D<-file.path(O,'plot_data');SUP<-file.path(O,'supplementary_vectors')
for(p in c(O,S,D,SUP,file.path(S,'proofs')))dir.create(p,recursive=TRUE,showWarnings=FALSE)
hash<-function(p)digest(readBin(p,'raw',n=file.info(p)$size),algo='sha256',serialize=FALSE)
inputs<-list();bindings<-list();figures<-list();supplement<-list()
read<-function(rel){p<-file.path(SRC,rel);inputs[[p]]<<-hash(p);read.csv(p,stringsAsFactors=FALSE,check.names=FALSE,fileEncoding='UTF-8-BOM')}
save_data<-function(df,id){p<-file.path(D,paste0(id,'.csv'));write.csv(df,p,row.names=FALSE,fileEncoding='UTF-8',na='');bindings[[id]]<<-list(path=p,rows=nrow(df),fields=names(df),sha256=hash(p))}
blue<-'#2166AC';orange<-'#B35806';ink<-'#272727';pale<-'#E7EAED'
theme_set(theme_classic(base_size=8.5,base_family='Arial')+theme(axis.text=element_text(size=8,colour=ink),axis.title=element_text(size=8.5),axis.line=element_line(linewidth=.3),axis.ticks=element_line(linewidth=.3),strip.text=element_text(size=8.5),strip.background=element_rect(fill='#F0F2F3',colour=NA),legend.title=element_text(size=8.5),legend.text=element_text(size=8),legend.position='bottom',plot.tag=element_text(size=10,face='bold'),plot.tag.position=c(0,1),plot.margin=margin(3,4,3,3),panel.spacing=grid::unit(3,'mm'),panel.grid=element_blank()))
short<-function(x)sub('^([A-Za-z])[a-z]+ ','\\1. ',x)
signed<-function(x)ifelse(is.na(x),'NA',ifelse(x==0,'0',ifelse(abs(x)<.01,ifelse(x>0,'+<.01','-<.01'),sprintf('%+.2f',x))))
text_col<-function(x,limit){z<-scales::gradient_n_pal(c(blue,'white',orange),values=c(0,.5,1),space='Lab')((x+limit)/(2*limit));z[is.na(z)]<-'grey75';r<-t(grDevices::col2rgb(z))/255;r<-ifelse(r<=.04045,r/12.92,((r+.055)/1.055)^2.4);L<-r%*%c(.2126,.7152,.0722);ifelse((L+.05)/.05>=1.05/(L+.05),'black','white')}
safe<-function(p){stopifnot(startsWith(tolower(normalizePath(p,winslash='/',mustWork=FALSE)),paste0(tolower(B),'/')));p}
export<-function(p,id,w=174,h=180,main=FALSE){
 folder<-if(main)file.path(O,id) else SUP;dir.create(folder,recursive=TRUE,showWarnings=FALSE);base<-file.path(folder,id)
 svglite::svglite(safe(paste0(base,'.svg')),width=w/25.4,height=h/25.4);print(p);dev.off()
 cairo_pdf(safe(paste0(base,'.pdf')),width=w/25.4,height=h/25.4,family='Arial');print(p);dev.off()
 ragg::agg_png(safe(paste0(base,'_WORD_300dpi.png')),width=w,height=h,units='mm',res=300,background='white');print(p);dev.off()
 ragg::agg_png(safe(paste0(base,'_PROOF_180dpi.png')),width=w,height=h,units='mm',res=180,background='white');print(p);dev.off()
 if(main){
  ragg::agg_tiff(safe(paste0(base,'_600dpi.tiff')),width=w,height=h,units='mm',res=600,compression='lzw',background='white');print(p);dev.off()
  cairo_ps(safe(paste0(base,'.eps')),width=w/25.4,height=h/25.4,family='Arial',onefile=FALSE,fallback_resolution=1200);print(p);dev.off()
 }
 info<-pdf_info(paste0(base,'.pdf'));stopifnot(info$pages==1)
 out<-list(id=id,pdf=paste0(base,'.pdf'),svg=paste0(base,'.svg'),word_png=paste0(base,'_WORD_300dpi.png'),proof_png=paste0(base,'_PROOF_180dpi.png'),width_mm=w,height_mm=h,main=main,pdf_sha256=hash(paste0(base,'.pdf')),svg_text_nodes=sum(grepl('<text',readLines(paste0(base,'.svg'),warn=FALSE),fixed=TRUE)))
 if(main)figures[[id]]<<-out else supplement[[id]]<<-out
 invisible(out)
}
# Historical prose-architecture lock is not a scientific figure input; upstream numerical validation is separate.
annual<-read('results/ground/ANNUAL_CHANGE_SUMMARY.csv');annual$sp<-factor(short(annual$species),levels=rev(short(annual$species)))
focal<-c('Fulica atra','Netta rufina');a<-annual[annual$species%in%focal,]
components<-rbind(data.frame(species=a$species,component='Frequency Cf',value=a$Cf),data.frame(species=a$species,component='Conditional count Cq',value=a$Cq));components$sp<-factor(short(components$species),levels=rev(short(focal)));a$sp<-factor(short(a$species),levels=rev(short(focal)));save_data(components,'F4a_GLOBAL_COMPONENTS')
p4a<-ggplot(components,aes(value,sp,fill=component))+geom_col(width=.55)+geom_vline(xintercept=0,linewidth=.3)+geom_point(data=a,aes(delta_mu,sp),inherit.aes=FALSE,shape=18,size=2.5)+scale_fill_manual(values=c('Frequency Cf'=blue,'Conditional count Cq'=orange))+labs(x='Annual mean change (recorded counts per slot)',y=NULL,fill=NULL)+theme(legend.position='top')
mass<-rbind(data.frame(species=annual$species,sp=annual$sp,value=annual$Pplus,direction='Positive positions'),data.frame(species=annual$species,sp=annual$sp,value=annual$Pminus,direction='Negative positions'));save_data(mass,'F4b_POSITION_SIGNED_MASSES')
p4b<-ggplot(mass,aes(value,sp,fill=direction))+geom_col(width=.65)+geom_vline(xintercept=0,linewidth=.3)+geom_point(data=annual,aes(delta_mu,sp),inherit.aes=FALSE,shape=18,size=2)+scale_fill_manual(values=c('Negative positions'=blue,'Positive positions'=orange))+labs(x='Contribution (counts per slot)',y=NULL,fill=NULL)+theme(legend.position='bottom',legend.direction='vertical',legend.key.height=grid::unit(2.3,'mm'))
win<-read('results/ground/WINDOW_CONTRIBUTIONS.csv');selected<-c('Fulica atra','Netta rufina','Phoenicopterus roseus','Platalea leucorodia','Phalacrocorax carbo');a<-win[win$species%in%selected,];a$sp<-factor(short(a$species),levels=rev(short(selected)));a$window<-factor(a$window,levels=c('DJF','MarMay','JunJul','SON'));a$label<-signed(a$signed_contribution);a$text_colour<-text_col(a$signed_contribution,max(abs(a$signed_contribution)));save_data(a,'F4c_WEIGHTED_WINDOW_CONTRIBUTIONS')
p4c<-ggplot(a,aes(window,sp,fill=signed_contribution))+geom_tile(colour='white',linewidth=.3)+geom_text(aes(label=label,colour=text_colour),size=8/ggplot2::.pt)+scale_colour_identity()+scale_fill_gradient2(low=blue,mid='white',high=orange,midpoint=0,name='Counts per slot')+scale_x_discrete(labels=c('DJF','Mar/May','Jun/Jul','SON'))+labs(x=NULL,y=NULL)+theme(axis.text.x=element_text(angle=55,hjust=1),legend.position='bottom')
p4a<-p4a+theme(axis.text.y=element_text(face='italic'));p4b<-p4b+theme(axis.text.y=element_text(face='italic'));p4c<-p4c+theme(axis.text.y=element_text(face='italic'))
p4a<-p4a+labs(tag='a');p4b<-p4b+labs(tag='b');p4c<-p4c+labs(tag='c')
F4<-(p4a/(p4b|p4c))+plot_layout(heights=c(.65,1.65),widths=c(1,1))
export(F4,'F4',h=175,main=TRUE)
# Figure5 uses only registered existing display summaries and annual records.
yp<-read('results/ground/YEARLY_PARENT_RECORDS.csv');pp<-read('results/concentration/PARENT_PERIOD_ENDPOINT_COMPARISON.csv');comp<-read('results/concentration/PERIOD_ENDPOINT_ANNUAL_COMPARISON.csv')
a<-yp[(yp$species=='Fulica atra'&yp$parent_name=='Marismas Del Rocío')|(yp$species=='Netta rufina'&yp$parent_name=='Dehesa De Abajo'),];a$case<-ifelse(a$species=='Fulica atra','Coot at Rocío','Red-crested pochard at Dehesa');save_data(a,'F5a_ANNUAL_NAMED_LOCALITY_RECORDS')
means<-pp[(pp$species=='Fulica atra'&pp$parent_name=='Marismas Del Rocío')|(pp$species=='Netta rufina'&pp$parent_name=='Dehesa De Abajo'),];means$case<-ifelse(means$species=='Fulica atra','Coot at Rocío','Red-crested pochard at Dehesa');m<-rbind(data.frame(case=means$case,period='2013-2017 mean',start=2013,end=2017,Y=means$Y_E),data.frame(case=means$case,period='2018-2023 mean',start=2018,end=2023,Y=means$Y_L));save_data(m,'F5a_PERIOD_MEAN_SEGMENTS')
p5a<-ggplot(a,aes(year,Y))+annotate('rect',xmin=2017.5,xmax=2023.3,ymin=-Inf,ymax=Inf,fill='#F1F2F3')+geom_line(linewidth=.35)+geom_point(size=1.2)+geom_segment(data=m,aes(x=start,xend=end,y=Y,yend=Y,colour=period,linetype=period),inherit.aes=FALSE,linewidth=.7)+facet_wrap(~case,nrow=1,scales='free_y')+scale_x_continuous(breaks=c(2013,2018,2023))+scale_colour_manual(values=c(blue,orange))+scale_linetype_manual(values=c('dashed','solid'))+labs(x='Calendar year',y='Annual locality Y',colour=NULL,linetype=NULL)+theme(legend.position='bottom')
chosen<-c('Marismas Del Rocío','Dehesa De Abajo','Gavetas','Balsas AB');a<-pp[pp$species%in%focal&pp$parent_name%in%chosen,];pn<-c('Marismas Del Rocío'='Rocío','Dehesa De Abajo'='Dehesa','Gavetas'='Gavetas','Balsas AB'='Balsas AB');a$case<-paste(ifelse(a$species=='Fulica atra','Coot','Pochard'),pn[a$parent_name],sep=' / ');levels5<-unlist(lapply(c('Coot','Pochard'),function(s)paste(s,unname(pn),sep=' / ')));a$case<-factor(a$case,levels=rev(levels5));save_data(a,'F5b_PERIOD_LOCALITY_CHANGES')
bb<-rbind(data.frame(case=a$case,value=a$annual_network_contribution,metric='Network mean contribution'),data.frame(case=a$case,value=a$delta_W*100,metric='Share change (percentage points)'))
p5b<-ggplot(bb,aes(value,case))+geom_vline(xintercept=0,colour='grey65',linewidth=.35)+geom_point(shape=16,size=1.8,colour=blue)+facet_wrap(~metric,nrow=1,scales='free_x')+labs(x=NULL,y=NULL)+theme(legend.position='none')
cc<-list();for(h in c('child','parent'))for(o in c('endpoint','period','annual_mean')){nm<-paste0('HHI_',h,'_',o,'_delta');a<-comp[comp$window=='ANNUAL'&comp$species%in%focal,c('species',nm)];names(a)[2]<-'delta';a$level<-h;a$object<-o;cc[[length(cc)+1]]<-a};cc<-do.call(rbind,cc);cc$sp<-factor(short(cc$species),levels=rev(short(focal)));cc$object<-factor(cc$object,levels=c('endpoint','period','annual_mean'));save_data(cc,'F5c_CONCENTRATION_TIME_OBJECTS')
p5c<-ggplot(cc,aes(delta,sp,shape=object,colour=object))+geom_vline(xintercept=0,colour='grey65',linewidth=.35)+geom_point(position=position_dodge(width=.55),size=2.2)+facet_wrap(~level,nrow=1)+scale_shape_manual(values=c(1,16,17),labels=c('2013 to 2023','Period distribution','Mean annual HHI'))+scale_colour_manual(values=c('grey50',blue,orange),labels=c('2013 to 2023','Period distribution','Mean annual HHI'))+labs(x='HHI change',y=NULL,shape=NULL,colour=NULL)+theme(legend.position='bottom',legend.key.width=grid::unit(4,'mm'))
p5c<-p5c+theme(axis.text.y=element_text(face='italic'))
F5<-(p5a/p5b/p5c)+plot_layout(heights=c(1.05,1.1,.72))+plot_annotation(tag_levels='a')
export(F5,'F5',h=195,main=TRUE)
# S4 full parent-month matrices. Grey/NA is unsupported membership; exact zero is white with0.
pm<-read('results/ground/PARENT_MONTH_CONTRIBUTIONS.csv');months<-c(1,2,3,5,6,7,9,10,11,12);parents<-unique(pm[,c('parent_code','parent_name')]);parents<-parents[order(parents$parent_code),];pl<-paste(parents$parent_code,parents$parent_name)
for(i in seq_along(annual$species)){
 sp<-annual$species[i];a<-pm[pm$species==sp,];gr<-expand.grid(parent_code=parents$parent_code,month=months,stringsAsFactors=FALSE);gr<-merge(gr,parents,by='parent_code',all.x=TRUE);a<-merge(gr,a,by=c('parent_code','parent_name','month'),all.x=TRUE);a$parent<-factor(paste(a$parent_code,a$parent_name),levels=rev(pl));a$month<-factor(a$month,levels=months);a$label<-signed(a$signed_contribution);a$species_strip<-sp;lim<-max(abs(a$signed_contribution),na.rm=TRUE);a$text_colour<-text_col(a$signed_contribution,lim)
 p<-ggplot(a,aes(month,parent,fill=signed_contribution))+geom_tile(colour='grey85',linewidth=.15)+geom_text(aes(label=label,colour=text_colour),size=8/ggplot2::.pt)+scale_colour_identity()+facet_wrap(~species_strip)+scale_fill_gradient2(low=blue,mid='white',high=orange,midpoint=0,limits=c(-lim,lim),na.value='grey75',name='Contribution (counts per slot)')+labs(x='Calendar month',y=NULL)+theme(axis.text.y=element_text(size=8),strip.text=element_text(face='italic'),legend.position='bottom',plot.margin=margin(3,2,3,2))
 export(p,sprintf('S4_%02d',i),h=210)
}
# S5 temporal objects and yearly series, all13.
cc<-list();for(h in c('child','parent'))for(o in c('endpoint','period','annual_mean')){nm<-paste0('HHI_',h,'_',o,'_delta');a<-comp[comp$window=='ANNUAL',c('species',nm)];names(a)[2]<-'delta';a$level<-h;a$object<-o;cc[[length(cc)+1]]<-a};cc<-do.call(rbind,cc);cc$sp<-factor(short(cc$species),levels=levels(annual$sp));cc$object<-factor(cc$object,levels=c('endpoint','period','annual_mean'))
p<-ggplot(cc,aes(delta,sp,shape=object,colour=object))+geom_vline(xintercept=0,colour='grey65')+geom_point(position=position_dodge(.5),size=2)+facet_wrap(~level,nrow=1)+scale_shape_manual(values=c(1,16,17),labels=c('2013 to 2023','Period distribution','Mean annual HHI'))+scale_colour_manual(values=c('grey50',blue,orange),labels=c('2013 to 2023','Period distribution','Mean annual HHI'))+labs(x='HHI change',y=NULL,shape=NULL,colour=NULL)
export(p+theme(axis.text.y=element_text(face='italic')),'S5_01',h=185)
yr<-read('results/concentration/YEARLY_HHI_AND_COMPONENTS.csv');a<-yr[yr$window=='ANNUAL',];lg<-rbind(data.frame(a[,c('species','year')],HHI=a$HHI_child,level='child'),data.frame(a[,c('species','year')],HHI=a$HHI_parent,level='parent'))
p<-ggplot(lg,aes(year,HHI,shape=level,colour=level))+geom_vline(xintercept=2017.5,linetype=2,colour='grey70')+geom_line(linewidth=.35)+geom_point(size=1)+facet_wrap(~species,ncol=3,scales='free_y')+scale_x_continuous(breaks=c(2013,2018,2023))+scale_colour_manual(values=c(blue,orange))+scale_shape_manual(values=c(16,1))+labs(x='Year',y='HHI',shape=NULL,colour=NULL)+theme(strip.text=element_text(size=8,face='italic'))
export(p,'S5_02',h=210)
# S6 all prespecified annual mean-change sensitivity, no new uncertainty model.
ss<-read('results/sensitivity/ANNUAL_SUMMARY_ALL_SCENARIOS.csv');rg<-aggregate(delta_mu~species,ss,function(x)c(min=min(x),max=max(x)));rg<-data.frame(species=rg$species,lo=rg$delta_mu[,1],hi=rg$delta_mu[,2]);rg<-merge(rg,annual[,c('species','delta_mu')],by='species');rg$sp<-factor(short(rg$species),levels=levels(annual$sp));save_data(rg,'S6_SCENARIO_ENVELOPES')
p<-ggplot(rg,aes(delta_mu,sp))+geom_vline(xintercept=0,colour='grey65')+geom_segment(aes(x=lo,xend=hi,yend=sp),colour=blue,linewidth=.8)+geom_point(shape=18,size=2.2)+labs(x='Annual mean change (counts per slot)',y=NULL)
export(p+theme(axis.text.y=element_text(face='italic')),'S6_01',h=180)
# S7 observed date offsets and same-species/structure descriptions.
dt<-read('results/cross_source/ACTUAL_DATE_MATCHED_VISITS.csv');dt<-dt[tolower(as.character(dt$kept_complete_event))=='true',]
pdate<-ggplot(dt,aes(signed_days))+geom_histogram(binwidth=1,boundary=.5,fill=blue,colour='white',linewidth=.15)+geom_vline(xintercept=0,linewidth=.3)+facet_wrap(~sector,nrow=1)+scale_x_continuous(breaks=c(-14,-7,0,7,14))+labs(x='Ground date minus aerial date (days)',y='Matched child visits')
co<-read('results/cross_source/SAME_SPECIES_TEMPORAL_CORRESPONDENCE.csv');co<-co[co$scenario%in%c('MAIN_14D','WITHIN7D'),];co$sp<-factor(short(co$species),levels=rev(unique(short(co$species))))
prho<-ggplot(co,aes(rho_departure,sp,shape=scenario,colour=scenario))+geom_vline(xintercept=0,colour='grey65')+geom_point(position=position_dodge(.4),size=2)+facet_wrap(~sector,nrow=1)+scale_colour_manual(values=c(blue,orange),labels=c('14 days','7 days'))+scale_shape_manual(values=c(16,17),labels=c('14 days','7 days'))+labs(x='Cross-source Spearman rho of native departures',y=NULL,shape=NULL,colour=NULL)
prho<-prho+theme(axis.text.y=element_text(face='italic'))
export((pdate/prho)+plot_layout(heights=c(.65,1))+plot_annotation(tag_levels='a'),'S7_01',h=195)
pair<-read('results/cross_source/SAME_EVENT_SPECIES_PAIR_STRUCTURE.csv');pair<-pair[pair$scenario=='MAIN_14D',];pair$adjustment<-factor(pair$adjustment,levels=c('NATIVE_DEPARTURE','WITHIN_YEAR_CENTERED','LINEAR_YEAR_RESIDUAL'))
p<-ggplot(pair,aes(air_rho,ground_rho,shape=sector,colour=sector))+geom_hline(yintercept=0,colour='grey80')+geom_vline(xintercept=0,colour='grey80')+geom_abline(slope=1,intercept=0,linetype=2,colour='grey65')+geom_point(size=1.7)+facet_wrap(~adjustment,ncol=2,labeller=as_labeller(c(NATIVE_DEPARTURE='Native departures',WITHIN_YEAR_CENTERED='Within-year centered',LINEAR_YEAR_RESIDUAL='Linear year residual')))+coord_equal(xlim=c(-1,1),ylim=c(-1,1))+scale_colour_manual(values=c(blue,orange))+scale_shape_manual(values=c(16,17))+labs(x='Aerial species-pair rho',y='Ground species-pair rho',shape=NULL,colour=NULL)
export(p,'S7_02',h=190)
# S8 same registered field-water relationship, existing category3 versus0 display and common-support control.
e<-read('results/environment/FIELD_WATER_FE_COEFFICIENTS.csv');e<-e[e$category==3,];lo<-read('results/environment/FIELD_WATER_FE_DELETE_YEAR.csv');lo<-lo[lo$category==3,];rg<-aggregate(estimate~species+response,lo,function(x)c(min=min(x),max=max(x)));rg$lo<-rg$estimate[,1];rg$hi<-rg$estimate[,2];rg$estimate<-NULL;e<-merge(e,rg,by=c('species','response'));e$sp<-factor(short(e$species),levels=levels(annual$sp));save_data(e,'S8_WATER_CATEGORY3_VS0')
p<-ggplot(e,aes(estimate,sp))+geom_vline(xintercept=0,colour='grey65')+geom_segment(aes(x=lo,xend=hi,yend=sp),colour=blue,linewidth=.7)+geom_point(shape=18,size=2)+facet_wrap(~response,nrow=1,scales='free_x',labeller=as_labeller(c(positive_log_count='Positive ln count',recorded_positive='Recorded positive')))+labs(x='Adjusted category3 versus0 contrast',y=NULL)
export(p+theme(axis.text.y=element_text(face='italic')),'S8_01',h=180)
st<-read('results/environment/COMMON_WATER_STANDARDIZED_PERIOD_RESULTS.csv');st<-st[st$metric=='mu',];st$sp<-factor(short(st$species),levels=levels(annual$sp));save_data(st,'S8_COMMON_WATER_STANDARDIZATION')
p<-ggplot(st,aes(same_common_strata_unstandardized_delta,sp))+geom_vline(xintercept=0,colour='grey65')+geom_segment(aes(xend=standardized_delta,yend=sp),colour='grey55')+geom_point(shape=1,size=2)+geom_point(aes(x=standardized_delta),shape=16,size=2,colour=blue)+labs(x='Period mean change (counts per slot)',y=NULL)
export(p+theme(axis.text.y=element_text(face='italic')),'S8_02',h=180)
# Pure-artwork multi-page PDFs for SI assembly.
for(group in c('S4','S5','S6','S7','S8')){ps<-vapply(supplement[startsWith(names(supplement),paste0(group,'_'))],function(x)x$pdf,character(1));pdf_combine(ps,output=file.path(SUP,paste0(group,'_COMPLETE.pdf')))}
old4<-file.path(INPUT_ROOT,'qa/Fig4_PreBridge.pdf')
old5<-file.path(INPUT_ROOT,'qa/Fig5_PreBridge.pdf')
historical_qa_available<-file.exists(old4)&&file.exists(old5)
if(historical_qa_available){
 inputs[[old4]]<-hash(old4);inputs[[old5]]<-hash(old5)
 pdf_combine(c(old4,figures$F4$pdf,old5,figures$F5$pdf),output=file.path(O,'F4_F5_OLD_NEW_COMPARISON_PROOF.pdf'))
}
write_json(list(historical_comparison=if(historical_qa_available)'AVAILABLE_PRIVATE_QA_INPUTS' else 'NOT_AVAILABLE_NOT_VERIFIED',scientific_inputs='NEW_BRIDGE_RESULTS'),file.path(S,'HISTORICAL_QA_AVAILABILITY.json'),pretty=TRUE,auto_unbox=TRUE)
for(id in names(figures)){
 f<-figures[[id]];pdf_convert(f$pdf,format='png',dpi=180,filenames=file.path(S,'proofs',paste0(id,'_ACTUAL_PDF_180dpi.png')),verbose=FALSE)
 im<-png::readPNG(f$proof_png);gray<-.2126*im[,,1]+.7152*im[,,2]+.0722*im[,,3];png::writePNG(gray,file.path(S,'proofs',paste0(id,'_GRAYSCALE.png')))
}
for(p in names(inputs))stopifnot(hash(p)==inputs[[p]])
write_json(list(backend='R_ONLY',figures=figures,supplementary_pages=supplement,inputs=inputs,display_data=bindings,source_protection='ALL_READ_INPUTS_UNCHANGED',new_analysis='NONE_ONLY_EXISTING_REGISTERED_DISPLAY_SELECTION_AND_AGGREGATION',EPS_independent_raster_verification='NOT_ESTABLISHED',session=capture.output(sessionInfo())),file.path(S,'FIGURE_PRODUCTION_AND_SOURCE_BINDINGS.json'),pretty=TRUE,auto_unbox=TRUE,digits=17)
cat('MAIN_FIGURES',length(figures),'SI_PAGES',length(supplement),'\n')

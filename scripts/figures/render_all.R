# Run only after the numerical pipeline produced bridge/results and the AIR interfaces.
script_arg <- grep('^--file=',commandArgs(),value=TRUE)
stopifnot(length(script_arg)==1)
script_dir <- dirname(normalizePath(sub('^--file=','',script_arg),winslash='/',mustWork=TRUE))
for(file in c('render_bridge_figures.R','render_fig4.R','render_fig5.R','render_fig23.R')){
  executable <- file.path(R.home('bin'),'Rscript.exe')
  if(!file.exists(executable))executable<-file.path(R.home('bin'),'Rscript')
  status<-system2(executable,c('--vanilla',shQuote(file.path(script_dir,file))))
  if(status!=0)stop(paste('Figure entry failed:',file,'exit',status))
}

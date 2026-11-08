# One explicit theme shared by original figure exports and review-PDF assembly.
ggplot2::theme_set(ggplot2::theme_classic(base_size=8.5,base_family='Arial')+ggplot2::theme(
 axis.line=ggplot2::element_line(linewidth=.3,colour='#4A4A4A'),axis.ticks=ggplot2::element_line(linewidth=.25),
 axis.text=ggplot2::element_text(colour='#303030',size=7.5),axis.title=ggplot2::element_text(size=8),
 plot.title=ggplot2::element_text(size=9,face='bold',hjust=0),plot.subtitle=ggplot2::element_text(size=8,colour='#444444'),
 strip.background=ggplot2::element_rect(fill='#F1F3F4',colour=NA),strip.text=ggplot2::element_text(size=8,face='italic'),
 legend.position='bottom',legend.text=ggplot2::element_text(size=8),legend.title=ggplot2::element_text(size=8),
 plot.margin=ggplot2::margin(5,6,5,6),plot.caption=ggplot2::element_text(size=7.5,hjust=0)))

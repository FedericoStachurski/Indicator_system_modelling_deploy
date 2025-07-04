import{p as E}from"./chunk-4BMEZGHF-DLcqo-x9.js";import{_ as c,g as G,s as L,a as N,b as P,q as V,p as q,l as O,c as H,E as I,I as _,O as J,d as K,y as Q,G as U}from"./mermaid-BgCxVw2J.js";import{p as X}from"./radar-MK3ICKWK-FyfW4UKQ.js";import"./transform-C5148Z0S.js";import{aF as y,aG as z,aH as Y,B as W,O as Z}from"./index-DlQKt39j.js";import"./_baseEach-DtUk7cBy.js";import"./_baseUniq-BuhsH2Gw.js";import"./min-DTkssK90.js";import"./_baseMap-zXgLfXUO.js";import"./clone-Cho8ekmu.js";import"./_createAggregator-CCTzDuxr.js";function ee(e,a){return a<e?-1:a>e?1:a>=e?0:NaN}function te(e){return e}var ae=U.pie,F={sections:new Map,showData:!1},M=F.sections,R=F.showData,ne=structuredClone(ae),B={getConfig:c(()=>structuredClone(ne),"getConfig"),clear:c(()=>{M=new Map,R=F.showData,Q()},"clear"),setDiagramTitle:q,getDiagramTitle:V,setAccTitle:P,getAccTitle:N,setAccDescription:L,getAccDescription:G,addSection:c(({label:e,value:a})=>{M.has(e)||(M.set(e,a),O.debug(`added new section: ${e}, with value: ${a}`))},"addSection"),getSections:c(()=>M,"getSections"),setShowData:c(e=>{R=e},"setShowData"),getShowData:c(()=>R,"getShowData")},re=c((e,a)=>{E(e,a),a.setShowData(e.showData),e.sections.map(a.addSection)},"populateDb"),ie={parse:c(async e=>{const a=await X("pie",e);O.debug(a),re(a,B)},"parse")},oe=c(e=>`
  .pieCircle{
    stroke: ${e.pieStrokeColor};
    stroke-width : ${e.pieStrokeWidth};
    opacity : ${e.pieOpacity};
  }
  .pieOuterCircle{
    stroke: ${e.pieOuterStrokeColor};
    stroke-width: ${e.pieOuterStrokeWidth};
    fill: none;
  }
  .pieTitleText {
    text-anchor: middle;
    font-size: ${e.pieTitleTextSize};
    fill: ${e.pieTitleTextColor};
    font-family: ${e.fontFamily};
  }
  .slice {
    font-family: ${e.fontFamily};
    fill: ${e.pieSectionTextColor};
    font-size:${e.pieSectionTextSize};
    // fill: white;
  }
  .legend text {
    fill: ${e.pieLegendTextColor};
    font-family: ${e.fontFamily};
    font-size: ${e.pieLegendTextSize};
  }
`,"getStyles"),le=c(e=>{const a=[...e.entries()].map(l=>({label:l[0],value:l[1]})).sort((l,d)=>d.value-l.value);return function(){var l=te,d=ee,u=null,w=y(0),S=y(z),$=y(0);function n(t){var r,s,i,A,m,p=(t=Y(t)).length,v=0,T=new Array(p),g=new Array(p),f=+w.apply(this,arguments),C=Math.min(z,Math.max(-z,S.apply(this,arguments)-f)),h=Math.min(Math.abs(C)/p,$.apply(this,arguments)),b=h*(C<0?-1:1);for(r=0;r<p;++r)(m=g[T[r]=r]=+l(t[r],r,t))>0&&(v+=m);for(d!=null?T.sort(function(x,D){return d(g[x],g[D])}):u!=null&&T.sort(function(x,D){return u(t[x],t[D])}),r=0,i=v?(C-p*b)/v:0;r<p;++r,f=A)s=T[r],A=f+((m=g[s])>0?m*i:0)+b,g[s]={data:t[s],index:r,value:m,startAngle:f,endAngle:A,padAngle:h};return g}return n.value=function(t){return arguments.length?(l=typeof t=="function"?t:y(+t),n):l},n.sortValues=function(t){return arguments.length?(d=t,u=null,n):d},n.sort=function(t){return arguments.length?(u=t,d=null,n):u},n.startAngle=function(t){return arguments.length?(w=typeof t=="function"?t:y(+t),n):w},n.endAngle=function(t){return arguments.length?(S=typeof t=="function"?t:y(+t),n):S},n.padAngle=function(t){return arguments.length?($=typeof t=="function"?t:y(+t),n):$},n}().value(l=>l.value)(a)},"createPieArcs"),se={parser:ie,db:B,renderer:{draw:c((e,a,l,d)=>{O.debug(`rendering pie chart
`+e);const u=d.db,w=H(),S=I(u.getConfig(),w.pie),$=18,n=450,t=n,r=_(a),s=r.append("g");s.attr("transform","translate(225,225)");const{themeVariables:i}=w;let[A]=J(i.pieOuterStrokeWidth);A??(A=2);const m=S.textPosition,p=Math.min(t,n)/2-40,v=W().innerRadius(0).outerRadius(p),T=W().innerRadius(p*m).outerRadius(p*m);s.append("circle").attr("cx",0).attr("cy",0).attr("r",p+A/2).attr("class","pieOuterCircle");const g=u.getSections(),f=le(g),C=[i.pie1,i.pie2,i.pie3,i.pie4,i.pie5,i.pie6,i.pie7,i.pie8,i.pie9,i.pie10,i.pie11,i.pie12],h=Z(C);s.selectAll("mySlices").data(f).enter().append("path").attr("d",v).attr("fill",o=>h(o.data.label)).attr("class","pieCircle");let b=0;g.forEach(o=>{b+=o}),s.selectAll("mySlices").data(f).enter().append("text").text(o=>(o.data.value/b*100).toFixed(0)+"%").attr("transform",o=>"translate("+T.centroid(o)+")").style("text-anchor","middle").attr("class","slice"),s.append("text").text(u.getDiagramTitle()).attr("x",0).attr("y",-200).attr("class","pieTitleText");const x=s.selectAll(".legend").data(h.domain()).enter().append("g").attr("class","legend").attr("transform",(o,k)=>"translate(216,"+(22*k-22*h.domain().length/2)+")");x.append("rect").attr("width",$).attr("height",$).style("fill",h).style("stroke",h),x.data(f).append("text").attr("x",22).attr("y",14).text(o=>{const{label:k,value:j}=o.data;return u.getShowData()?`${k} [${j}]`:k});const D=512+Math.max(...x.selectAll("text").nodes().map(o=>(o==null?void 0:o.getBoundingClientRect().width)??0));r.attr("viewBox",`0 0 ${D} 450`),K(r,n,D,S.useMaxWidth)},"draw")},styles:oe};export{se as diagram};

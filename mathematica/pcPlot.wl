(* ::Package:: *)

(* :Name: pcPlot` *)
(* :Author: Hongzhe Zhou, Stockholm, 2021*)
(* :Version: 0.1 *)
(* :Summary:
    Define general plot styles, and functions that make 2D plots.
*)


BeginPackage["pcPlot`","pcReadBasic`","pcRead1D`","pcRead2D`","pcUtils`"]


(* ::Chapter:: *)
(*Usage messages*)


pcHexColor::usage="Takes in a Hex color code and outputs the color."
pcColors::usage="Some self-defined colors. Use pcColors[colorName,{min,max}] for a data set where
0 will always be rescaled to 0.5, and the larger one in Abs[min] and max will be rescaled to 0 or 1.
Useful when plotting butterfly diagrams etc."
pcLabelStyle::usage="Font and size.";
pcPlotStyle::usage="Set some plot styles.";
pcPopup::usage="Using DisplayFunction->pcPopup will make a plot in a pop-up window."

pcTicks::usage="Frame ticks in convenient forms."

pcInset::usage="pcInset[str,posx,posy] is equivalent to
Inset[Style[str,pcLabelStyle],Scaled[{posx,posy}]]."

pcLegend::usage="pcLegend[l,opts] uses DensityPlot to make a bar legend.
Input:
  l: List. MinMax[l] will specify the lower and upper bounds of the data.
Options:
  opts: Will be inherited by DensityPlot and overwrite the default ones.
        Usually one needs to adjust ImageSize, ImagePadding, and AspectRatio to have
        the best looking.
Output:
  A bar legend as an Image object, which can be aligned with other figures using Grid."

pcDensityPlot::usage="pcDensityPlot[data] plots 2D color plots using ArrayPlot. It has better performance
than ListDensityPlot and should be generally used on equidistant grids.
Input:
  data: Can either be a Nx by 3 List {gridx,gridy,gridf} or its Transpose. Need not be Sort'ed.
Options:
  All options inherit those of ArrayPlot."

pcPolarDensityPlot::usage="pcPolarDensityPlot[r,theta,f,opts] plots 2D color plots in the polar coordinates
using Graphics combined with Annulus. It has better performance than using ListDensityPlot.
Input:
  r: The radial coordinates. E.g., readGrid[sim][[1]].
  theta: The polar coordinates. E.g., readGrid[sim][[2]].
  f: A 2D array of dimension {Length[r],Length[theta]}.
Options:
  \"DataOptions\" should be a List with the following possible Rules:
    \"DownSamplingFractions\": A List with two positive real numbers {dsr,dsth}, to down-sample data.
    \"ColorFunction\": Could be ColorData[...] or pcColors[...]. The default is pcColors[\"Rainbow\"].
  \"PlotOptions\" will be inherited by the output Graphics[...].
Example:
  pcPolarDensityPlot[{r,theta,lnrho},\[IndentingNewLine]    \"DataOptions\"->{\"DownSamplingFractions\"->{2,3},\"ColorFunction\"->ColorData[\"BlueGreenYellow\"]},\[IndentingNewLine]    \"PlotOptions\"->{FrameLabel->{\"x\",\"y\"}}\[IndentingNewLine]  ]"

pcLICPlot::usage="pcLICPlot[array,regionFunc,opts] is a wrapper for ListLineIntegralConvolutionPlot.
Input:
  array: A List of form { {{x,y},{vx,vy}},... }.
  regionFunc: Optional. This should be a Function like
                Between[Norm[{#1,#2}],r//MinMax] && Between[ArcCos[#2/Norm[{#1,#2}]],theta//MinMax] &
              which specifies which region should be plotted, as a temporary solution since there is
              no RegionFunction option for ListLineIntegralConvolutionPlot. The arguments of regionFunc
              are x and y.
  opts: Options that will be inherited by ListLineIntegralConvolutionPlot."

spaceTimeDiag::usage="spaceTimeDiag[sim,plane,var,plotStyle:] makes a butterfly diagram from planar averaged data.
Input:
  sim: String. Directory of the simulation.
  plane: String. \"xy\" or \"yz\" or \"xz\", specifying which plane is averaged over.
  var: String. Must be present in \"xyaver.in\" etc.
  plotStyle: Optional. Can be several Rule objects. Will overwrite the default plot styles.
Output:
  A space-time diagram with 1/3 aspect ratio, and time coordinates in code units. The space cooridnates
are normalized to (-1,1). Also print out the MinMax values of the data for the possibility of making
legends by hand."

showSlice::usage="showSlice[data,var,{sp,loc},plotStyle:] plots a slice.
Input:
  data: Must be from readVARN[sim,iVAR].
  var: String. Variable to read; e.g. \"uu1\".
  sp: String. \"x\", \"y\", or \"z\".
  loc: Numeric. Will plot the slice closest to this position.
  plotStyle: Optional. Will overwrite the current style of ListDensityPlot.
Output:
  A density plot of var at location loc in the sp direction"

showSliceVector::usage="showSliceVector[data,var,{sp,loc},plotStyle:] plots a vector field
  in the slice spcified by sp and loc. The in-plane componets are shown as arrows, and the
  out-of-plane componet is shown in a density map.
Input:
  data: Must be from readVARN[sim,iVAR]
  var: String. Variable to read; e.g. \"uu\" or \"bbb\"
  sp: String. \"x\", \"y\", or \"z\"
  loc: Numeric. Will plot the slice closest to this position.
  plotStyle: Optional. Will overwrite the current plotting style.
Output:
  A vector plot of var at location loc in the sp direction"

pcPanelDataPlot::usage="pcPanelDataPlot[data,{m,n},style:{},Options] makes a plot of m times n panels,
with shared axes.
Input:
  data: List. Each element should be a data set like {{x1,y1},{x2,y2},...}.
  {m,n}: m columns and n rows. Better to have m*n=Length[data].
  style: List. Optional. User-specified plot styles for all panels.
Options:
  \"ImageSize0\" by default 300. The ImageSize for each individual panel.
  \"ImagePadding0\" by default {45,6}. The ImagePadding for each individual panel.
      The first number specifies the ones with frame labels, and the second number
      specifies the ones without frame labels.
  \"Spacing\" by default {0.2,0.5}. The horizontal and vertical spacings between panels."

pcPanelPlot::usage="pcPanelPlot[plots,{m,n},Options] makes a plot of m times n panels,
with shared axes.
Input:
  plots: A List of plots. Can already have FrameTicks.
  {m,n}: m columns and n rows. Better to have m*n=Length[plots].
Options:
  \"ImageSize0\" by default 300. The ImageSize for each individual panel.
  \"ImagePadding0\" by default 25. The ImagePadding for each individual panel.
  \"Spacing\" by default {0.2,0.5}. The horizontal and vertical spacings between panels."


Begin["`Private`"]


(* ::Chapter:: *)
(*Functions*)


(* ::Section:: *)
(*Self-defined colors*)


pcHexColor[hex_]:=RGBColor@@(IntegerDigits[ToExpression@StringReplace[hex,"#"->"16^^"],256,3]/255.)

pcColors[cf_Function]:=cf
pcColors[name_String]:=Switch[name,
  "Red",RGBColor[{166,42,23}/255],
  "Blue",RGBColor[{28,77,124}/255],
  "Green",RGBColor[{1,113,0}/255],
  "Magenta",RGBColor[{151,14,83}/255],
  "Rainbow",Blend[{pcHexColor["#032D75"],pcHexColor["#01B1FA"],pcHexColor["#F4BD18"],pcHexColor["#ED1B24"]},#]&,
  "RainbowR",Blend[Reverse@{pcHexColor["#032D75"],pcHexColor["#01B1FA"],pcHexColor["#F4BD18"],pcHexColor["#ED1B24"]},#]&,
  (*"RainbowR",ColorData[{"Rainbow","Reversed"}],*)
  "BlueBlackRed",Blend[{pcColors["Blue"],pcHexColor["#006C65"],Black,pcHexColor["#E2792E"],pcColors["Red"]},#]&,
  "BlueWhiteRed",Blend[{pcColors["Blue"],pcHexColor["#6C96CC"],pcHexColor["#EDAE92"],pcColors["Red"]},#]&,
  _,ColorData[name]
]
pcColors[name_String,{min_,max_}]:=pcColors[name][If[Abs[min]>=max,-0.5/min*(#-min),0.5/max*(#-max)+1]]&/;NumericQ[min]&&NumericQ[max]
pcColors[cf_,list_List]:=pcColors[cf]/@Rescale[list//Length//Range]


(* ::Section:: *)
(*Plot style related*)


pcLabelStyle=Directive[AbsoluteThickness[1],Black,14,FontFamily->"Times"];
pcPlotStyle[]:=Module[{setOps},
  setOps[ops_List,funcs_List]:=Map[SetOptions[#,ops]&,funcs];
  (*General options for all plots*)
  setOps[{
      PlotRange->All,Frame->True,Axes->None,LabelStyle->pcLabelStyle,
      FrameStyle->pcLabelStyle,ImageSize->{360,360/GoldenRatio},
      ImagePadding->{{50,50},{50,10}}
    },{
      Plot,LogPlot,LogLogPlot,LogLinearPlot,DensityPlot,
      ListPlot,ListLogPlot,ListLogLogPlot,ListLogLinearPlot,ListLinePlot,
      ListDensityPlot,ListVectorPlot,ListStreamPlot,ListLineIntegralConvolutionPlot,
      Histogram,SmoothHistogram
    }];
  (*Options for 1D plots*)
  setOps[{
      Method->"DefaultPlotStyle"->Directive[Black,AbsoluteThickness[1]]
    },{
      Plot,LogPlot,LogLogPlot,LogLinearPlot,
      ListPlot,ListLogPlot,ListLogLogPlot,ListLogLinearPlot,ListLinePlot,
      SmoothHistogram
    }];
  (*Options for 1D List plots*)
  setOps[{
      Joined->True
    },{
      ListPlot,ListLogPlot,ListLogLogPlot,ListLogLinearPlot,ListLinePlot
    }];
  (*Options for 2D plots*)
  setOps[{
      PlotLegends->Automatic,ColorFunction->pcColors["Rainbow"],
      PlotRangePadding->None
    },{
      DensityPlot,ListDensityPlot,ListLineIntegralConvolutionPlot
    }];
  setOps[{
      RegionBoundaryStyle->None,RegionFillingStyle->None
    },{
      ListVectorPlot,ListStreamPlot,ListVectorDensityPlot,ListStreamDensityPlot
    }];
  (*Options for ListDensity Plot*)
  setOps[{
      InterpolationOrder->0
    },{
      ListDensityPlot
    }];
]

pcPopup[plot_]:=CreateDocument[plot,
  "CellInsertionPointCell"->Cell,ShowCellBracket->False,
  WindowElements->{},WindowFrame->"Generic",WindowSize->All,
  WindowTitle->None,WindowToolbars->{}
]

pcTicks["10^i",max_:99]:=Table[{10^i,Superscript["10",ToString@i]},{i,-max,max}]
pcTicks["Log10i",max_:99]:=Table[{10^i,ToString@i},{i,-max,max}]
pcTicks["Range"][range_,pd_]:=List[
  {#,StringPadRight[ToString[#],pd,"0"]}&/@range, Automatic
]
pcTicks["Range2"][minmax_]:=Module[{mean,d,r,ticks},
  d=-Subtract@@minmax/4*0.9;
  r=Min[1,10.^Floor[Log10[d]]];
  d=Round[d,r];
  mean= minmax//Mean//Round[#,r]&;
  ticks=mean+d*Range[-2,2];
  ReplaceAll[ticks,x_/;StringEndsQ[ToString[x],"."]:>{x,ToString[x]<>"0"}]
]

pcInset[str_String,posx_,posy_]:=Inset[Style[str,pcLabelStyle],Scaled[{posx,posy}]]


(* ::Section:: *)
(*Bar legend*)


pcLegend[l_List,opt:OptionsPattern[]]:=Module[{data,minmax},
  minmax=l//MinMax;
  data=Table[{x,y,y},{x,{0,1}},{y,Subdivide[Sequence@@minmax,127]}]//Flatten[#,1]&;
  pcDensityPlot[data,opt,
    ColorFunction->pcColors["Rainbow"],PlotLegends->None,
    FrameTicks->{{None,pcTicks["Range2"][minmax]},{None,None}},PlotRangePadding->None,
    AspectRatio->12,ImagePadding->{{5,40},{5,5}},ImageSize->{80,240},
    FrameTicksStyle->Automatic
  ]
];

pcLegend[l_List,"h",opt:OptionsPattern[]]:=Module[{data,minmax},
  minmax=l//MinMax;
  data=Table[{x,y,x},{x,Subdivide[Sequence@@minmax,127]},{y,{0,1}}]//Flatten[#,1]&;
  pcDensityPlot[data,
    ColorFunction->ColorData[{"Rainbow","Reversed"}],PlotLegends->None,
    FrameTicks->{{None,None},{pcTicks["Range2"][minmax],None}},PlotRangePadding->None,
    AspectRatio->1/12,ImagePadding->{{5,5},{40,5}},ImageSize->{240,80}
  ]
]


(* ::Section:: *)
(*Wrapper for ArrayPlot*)


(* to-do: All places where ListDensityPlot is used for a equidistant grid, for better performance *)
pcDensityPlot[{gridx_,gridy_,data_},opts:OptionsPattern[]]:=Module[{x,y,f,frameLabel},
  {x,y,f}=Transpose[{gridx,gridy,data}]//Sort//Transpose;
  f=Reverse[Transpose@Partition[f,y//Union//Length]];
  
  (* by default ArrayPlot will transpose the xy frame labels; here is a fix *)
  frameLabel=With[{op=Association[opts]},
    If[KeyExistsQ[op,FrameLabel],
      If[Length[op[FrameLabel]]==2,Reverse[op[FrameLabel]],op[FrameLabel]],
      None
    ]
  ];
  ArrayPlot[f,FrameLabel->frameLabel,opts,
    DataRange->{x//MinMax,y//MinMax},
    AspectRatio->Abs[(Subtract@@MinMax[y])/(Subtract@@MinMax[x])],
    PlotRangePadding->None,ColorFunction->pcColors["Rainbow"],
    FrameTicks->{{Subdivide[Sequence@@MinMax[y],4],Automatic},{Subdivide[Sequence@@MinMax[x],4],Automatic}},
    FrameStyle->Directive[Black,AbsoluteThickness[1]],
    FrameTicksStyle->ConstantArray[{pcLabelStyle,Directive[FontOpacity->0,FontSize->0]},2],
    LabelStyle->pcLabelStyle,PlotLegends->Automatic
  ]
]
pcDensityPlot[data_List,opts:OptionsPattern[]]:=pcDensityPlot[Transpose[data],opts]/;Dimensions[data][[-1]]==3


(* ::Section:: *)
(*Density plot in polar coordinates*)


Options[pcPolarDensityPlot]={"DataOptions"->{},"PlotOptions"->{Frame->True}};
pcPolarDensityPlot[{r0_List,theta0_List,f0_List},OptionsPattern[]]:=Module[{optsD,optsP,dsr,dsth,r,th,f,minmax,cf,dr,dth,ann},
  optsD=Association[OptionValue["DataOptions"]];
  optsP=Association[OptionValue["PlotOptions"]];
  
  (* remap polar angle from [0,\[Pi]] to [\[Pi]/2,-\[Pi]/2] *)
  r=r0;
  th=Reverse[\[Pi]/2-theta0];
  f=Reverse/@f0;
  
  (* down-sampling fractions *)
  (* e.g. If dsr==2 then down-sample r direction every 2 mesh points *)
  {dsr,dsth}=Lookup[optsD,"DownSamplingFactor",{1,1}];
  r=ArrayResample[r,Scaled[1/dsr]];
  th=ArrayResample[th,Scaled[1/dsth]];
  f=ArrayResample[f,Scaled[1/#]&/@{dsr,dsth}];
  dr=1.02*Flatten@{0,r//Differences,0};
  dth=1.02Flatten@{0,th//Differences,0};
  
  (* color function *)
  minmax=Lookup[optsP,PlotRange,f//Flatten//MinMax];
  cf[x_]:=Lookup[optsP,ColorFunction,pcColors["Rainbow"]]@Rescale[x,minmax];
  
  (* generate cells *)
  ann=Table[
    {EdgeForm[],cf[f[[i,j]]],Annulus[{0,0},{r[[i]]-dr[[i]]/2,r[[i]]+dr[[i+1]]/2},{th[[j]]-dth[[j]]/2,th[[j]]+dth[[j+1]]/2}]},
    {i,1,r//Length},{j,1,th//Length}
  ]//Flatten[#,1]&;
  
  (* plot *)
  Graphics[ann,
    DeleteCases[OptionValue["PlotOptions"], ( ColorFunction | PlotRange )->_],
    Frame->True,LabelStyle->pcLabelStyle,FrameStyle->pcLabelStyle,
    ImagePadding->{{50,50},{50,10}},Background->Transparent
  ]
]


(* ::Section:: *)
(*Wrapper for ListLineIntegralConvolutionPlot*)


pcLICPlot[arr_,regionFunc_Function:(True&),opts:OptionsPattern[]]:=Module[{minmax,mask},
  minmax["x"]=arr[[;;,1,1]]//MinMax;
  minmax["y"]=arr[[;;,1,2]]//MinMax;
  minmax["norm"]=MinMax[Norm/@(arr[[;;,2]])];
  
  mask=RegionPlot[Not[regionFunc[x,y]],{x,Sequence@@minmax["x"]},{y,Sequence@@minmax["y"]},
    PlotStyle->White, BoundaryStyle->None
  ];
  
  Show[
    ListLineIntegralConvolutionPlot[arr,opts,
      AspectRatio->Differences[minmax["x"]]/Differences[minmax["y"]],
      ColorFunctionScaling->False,
      ColorFunction->Function[{x,y,vx,vy,n},ColorData["BlueGreenYellow"][Rescale[n//Log10,minmax["norm"]//Log10]]],
      LightingAngle->{0,Pi/2}
    ],
    mask
  ]
]


(* ::Section:: *)
(*Butterfly diagram*)


spaceTimeDiag[sim_,sl_,var_,plotStyle___Rule]:=Module[{t,f,nt,nx,gf},
  PrintTemporary["Reading data..."];
  {t,f}=readAves[sim,sl,var];
  {nt,nx}=Dimensions[f];

  gf=f[[1;;-1;;Ceiling[nt/nx/3],;;]]//Transpose;
  Print["The MinMax of data is ",gf//Flatten//MinMax];

  PrintTemporary["Making plots..."];
  ListDensityPlot[gf,plotStyle,
    DataRange->{t[[{1,-1}]],{-1,1}},
    AspectRatio->1/3,InterpolationOrder->0
  ]
]


(* ::Section:: *)
(*Plot a slice from a readVARN[sim,iVAR] data*)


showSlice[data_,var_String,{sp_String,loc_?NumericQ},opts:OptionsPattern[]]:=
  Module[{f,x1,x2,x3,x30,pos,plotData},
    f=data[var];
    {x1,x2,x3}=data/@Switch[sp,
        "x",{"y","z","x"},"y",{"x","z","y"},"z",{"x","y","z"}
      ];
    x30=Nearest[x3//Union,loc][[1]];
    pos=Position[x3,x30];
    Print["Plotting the slice at ",sp,"=",x30];
    plotData=Transpose[Extract[#,pos]&/@{x1,x2,f}];
    pcDensityPlot[plotData,opts]
  ]

(*plot from VAR data*)
showSliceVector[data_Association,var_String,{sp_String,loc_?NumericQ},plotStyle___Rule]:=
  Module[{f1,f2,f3,x1,x2,x3,r,pos,x12,v12,vecData,denData},
    {f1,f2,f3}=data[var<>ToString@#]&/@Switch[sp,
      "x",{2,3,1},"y",{1,3,2},"z",{1,2,3}
    ];
    {x1,x2,x3}=data/@Switch[sp,
      "x",{"y","z","x"},"y",{"x","z","y"},"z",{"x","y","z"}
    ];
    r=Abs[(Subtract@@MinMax[x2])/(Subtract@@MinMax[x1])];
    pos=Nearest[x3->"Index",loc];
    Print["Plotting the slice at ",sp,"=",x3[[pos//First]]];
    Print["Plotting range of the out-of-plane component: ",MinMax[f3]];
    x12=Transpose[Extract[#,List/@pos]&/@{x1,x2}];
    v12=Transpose[Extract[#,List/@pos]&/@{f1,f2}];
    vecData=Transpose[{x12,v12}];
    denData=Flatten/@Transpose[{x12,Extract[f3,List/@pos]}];
    Show[
      ListDensityPlot[denData],
      ListVectorPlot[vecData,VectorScaling->"Linear",
        VectorColorFunction->None,VectorStyle->White],
      plotStyle,AspectRatio->r,ImageSize->Medium
    ]
]


(* ::Section:: *)
(*Plot multiple panels with shared axes*)


Options[pcPanelDataPlot]={"ImageSize0"->300,"ImagePadding0"->25,"Spacingx"->-2}
pcPanelDataPlot[data_,{m_,n_},style_List:{},OptionsPattern[]]:=Module[{
  nData,lpos,shift,xRange,yRange,styleAll,
  tkStyle,imgPd,imgSz,imgSz0,imgPd0,spx},
  pcPanelDataPlot::nonrect="Warning: The bottom ticks may show incorrectly.";
  pcPanelDataPlot::insuffpanel="Error: Insufficient number of panels specified.";
  nData=Length[data];
  If[m*n<nData,Message[pcPanelDataPlot::insuffpanel];Return[$Failed]];
  If[m*n!=nData,Message[pcPanelDataPlot::nonrect]];
  
  imgSz0=OptionValue["ImageSize0"];
  imgPd0=OptionValue["ImagePadding0"];
  spx=OptionValue["Spacingx"];
  lpos[i_]:=List[
    (*left and right*)
    {MemberQ[Range[1,m*n,m],i],MemberQ[Range[m,m*n,m],i]},
    (*bottom and top*)
    {MemberQ[Range[m*n-m+1,m*n],i],(*MemberQ[Range[1,m],#]*)False}
  ];
  
  (*overall plot styles*)
  shift[{x1_,x2_}]:={x1-0.1(x2-x1),x2+0.1(x2-x1)};
  xRange=data[[;;,;;,1]]//Flatten//MinMax//shift;
  yRange=data[[;;,;;,2]]//Flatten//MinMax//shift;
  styleAll={style,ImageSize->imgSz0,PlotRange->{xRange,yRange},FrameTicks->True,FrameTicksStyle->pcLabelStyle};
  
  (*individual plot styles*)
  tkStyle[i_]:=(FrameTicksStyle->Map[Directive[FontOpacity->#]&,lpos[i]/.{True->1,False->0},{2}]);
  imgPd[i_]:=(ImagePadding->(lpos[i]/.{True->imgPd0,False->1}));
  imgSz[i_]:=Module[{w=imgSz0,h=imgSz0/GoldenRatio},
    If[!lpos[i][[1,1]],w=w-imgPd0];If[!lpos[i][[1,2]],w=w-imgPd0];
    If[!lpos[i][[2,1]],h=h-imgPd0];If[!lpos[i][[2,2]],h=h-imgPd0];
    ImageSize->{w,h}
  ];
  
  Table[ListPlot[data[[i]],tkStyle[i],imgPd[i],imgSz[i],styleAll],{i,nData}]//Partition[#,UpTo@m]&//Grid[#,Spacings->{spx,0.5}]&
]


Options[pcPanelPlot]={"ImageSize0"->300,"ImagePadding0"->{45,6},"Spacing"->{0.2,0.5}}
pcPanelPlot[plots_,{m_,n_},OptionsPattern[]]:=Module[{
  nData,lpos,ladd,tkStyle,imgPd,imgSz,imgSz0,imgPd0,spxy},
  pcPanelPlot::insuffpanel="Error: Insufficient number of panels specified.";
  nData=Length[plots];
  If[m*n<nData,Message[pcPanelPlot::insuffpanel];Return[$Failed]];
  ladd=If[m*n!=nData,True,False];
  
  imgSz0=OptionValue["ImageSize0"];
  imgPd0=OptionValue["ImagePadding0"];
  spxy=OptionValue["Spacing"];
  lpos[i_]:=List[
    (*left and right*)
    {MemberQ[Range[1,m*n,m],i],MemberQ[Range[m,m*n,m],i]},
    (*bottom and top*)
    {MemberQ[Range[m*n-m+1,m*n],i]||And[ladd,MemberQ[Range[nData-m+1,m*(n-1)],i]],
    (*MemberQ[Range[1,m],#]*)False}
  ];
  
  (*individual plot styles*)
  tkStyle[i_]:=(FrameTicksStyle->Map[Directive[FontOpacity->#]&,lpos[i]/.{True->1,False->0},{2}]);
  imgPd[i_]:=(ImagePadding->(lpos[i]/.{True->imgPd0[[1]],False->imgPd0[[2]]}));
  imgSz[i_]:=Module[{w=imgSz0,h=imgSz0/GoldenRatio},
    If[!lpos[i][[1,1]],w=w-imgPd0];If[!lpos[i][[1,2]],w=w-imgPd0];
    If[!lpos[i][[2,1]],h=h-imgPd0];If[!lpos[i][[2,2]],h=h-imgPd0];
    ImageSize->{w,h}
  ];
  
  Table[Show[plots[[i]],tkStyle[i],imgPd[i],imgSz[i]],{i,nData}]//Partition[#,UpTo@m]&//Grid[#,Spacings->spxy,Alignment->Top]&
]


(* ::Chapter:: *)
(*End*)


End[]


Protect[
  pcHexColor,pcColors,
  pcLabelStyle,pcPlotStyle,pcPopup,pcTicks,pcInset,
  pcLegend,
  pcDensityPlot,pcPolarDensityPlot,pcLICPlot,
  spaceTimeDiag,
  showVideo,
  showSlice,showSliceVector,
  pcPanelDataPlot,pcPanelPlot
]


EndPackage[]

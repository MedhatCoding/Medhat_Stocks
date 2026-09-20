
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

void main()=>runApp(const App());
class Api{
 static const base=String.fromEnvironment('API_BASE',defaultValue:'http://10.0.2.2:8000');
 static Future<dynamic> get(String p)async{final r=await http.get(Uri.parse(base+p)).timeout(const Duration(seconds:35));final b=jsonDecode(r.body);if(r.statusCode>=400)throw Exception(b['detail']??'تعذر الاتصال');return b;}
 static Future<dynamic> post(String p)async{final r=await http.post(Uri.parse(base+p)).timeout(const Duration(seconds:50));final b=jsonDecode(r.body);if(r.statusCode>=400)throw Exception(b['detail']??'تعذر الاتصال');return b;}
}
class App extends StatefulWidget{const App({super.key});@override State<App>createState()=>_AppState();}
class _AppState extends State<App>{bool dark=true;@override void initState(){super.initState();SharedPreferences.getInstance().then((p){if(mounted)setState(()=>dark=p.getBool('dark')??true);});}Future<void>theme(bool v)async{final p=await SharedPreferences.getInstance();await p.setBool('dark',v);if(mounted)setState(()=>dark=v);}@override Widget build(BuildContext c)=>MaterialApp(debugShowCheckedModeBanner:false,title:'مدحت ستوكس',locale:const Locale('ar'),supportedLocales:const[Locale('ar')],themeMode:dark?ThemeMode.dark:ThemeMode.light,theme:ThemeData(useMaterial3:true,colorScheme:ColorScheme.fromSeed(seedColor:const Color(0xFF0B8F87))),darkTheme:ThemeData(useMaterial3:true,brightness:Brightness.dark,colorScheme:ColorScheme.fromSeed(seedColor:const Color(0xFF0B8F87),brightness:Brightness.dark)),home:Shell(onTheme:theme));}
class Shell extends StatefulWidget{final Future<void>Function(bool)onTheme;const Shell({super.key,required this.onTheme});@override State<Shell>createState()=>_ShellState();}
class _ShellState extends State<Shell>{
 int i=0;
 @override Widget build(BuildContext c){
  final pages=[Home(go:(x)=>setState(()=>i=x)),const Opportunities(),const Search(),const Watchlist(),const Portfolio()];
  return Scaffold(
   drawer:Drawer(child:SafeArea(child:ListView(children:[
    const DrawerHeader(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Icon(Icons.auto_graph,size:42),SizedBox(height:10),Text('مدحت ستوكس',style:TextStyle(fontSize:25,fontWeight:FontWeight.w900)),Text('مساعد شخصي لتحليل EGX')])),
    ListTile(leading:const Icon(Icons.bolt),title:const Text('الفرص'),onTap:(){Navigator.pop(c);setState(()=>i=1);}),
    ListTile(leading:const Icon(Icons.search),title:const Text('تحليل سهم'),onTap:(){Navigator.pop(c);setState(()=>i=2);}),
    ListTile(leading:const Icon(Icons.star),title:const Text('المتابعة'),onTap:(){Navigator.pop(c);setState(()=>i=3);}),
    ListTile(leading:const Icon(Icons.account_balance_wallet),title:const Text('المحفظة'),onTap:(){Navigator.pop(c);setState(()=>i=4);}),
    ListTile(leading:const Icon(Icons.settings_outlined),title:const Text('الإعدادات'),onTap:(){Navigator.pop(c);Navigator.push(c,MaterialPageRoute(builder:(_)=>SettingsPage(onTheme:widget.onTheme)));}),
    SwitchListTile.adaptive(value:Theme.of(c).brightness==Brightness.dark,onChanged:widget.onTheme,title:const Text('الوضع الداكن'),secondary:const Icon(Icons.dark_mode_outlined)),
   ]))),
   body:SafeArea(child:IndexedStack(index:i,children:pages)),
   bottomNavigationBar:NavigationBar(selectedIndex:i,onDestinationSelected:(x)=>setState(()=>i=x),destinations:const[
    NavigationDestination(icon:Icon(Icons.home_outlined),label:'الرئيسية'),
    NavigationDestination(icon:Icon(Icons.bolt_outlined),label:'الفرص'),
    NavigationDestination(icon:Icon(Icons.search),label:'تحليل'),
    NavigationDestination(icon:Icon(Icons.star_outline),label:'المتابعة'),
    NavigationDestination(icon:Icon(Icons.account_balance_wallet_outlined),label:'المحفظة'),
   ]),
  );
 }
}
class Home extends StatefulWidget{final ValueChanged<int>go;const Home({super.key,required this.go});@override State<Home>createState()=>_HomeState();}
class _HomeState extends State<Home>{Map<String,dynamic>?m;List<dynamic>o=[];@override void initState(){super.initState();load();}Future<void>load()async{try{final r=await Future.wait([Api.get('/market/context'),Api.get('/opportunities?limit=5')]);if(mounted)setState(() { m=r[0]; o=r[1]['data']??[]; });}catch(_){}}@override Widget build(BuildContext c)=>RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.all(18),children:[Row(children:[Builder(builder:(x)=>IconButton(onPressed:()=>Scaffold.of(x).openDrawer(),icon:const Icon(Icons.menu,size:28))),const Expanded(child:Text('مدحت ستوكس',style:TextStyle(fontSize:28,fontWeight:FontWeight.w900))),IconButton(onPressed:load,icon:const Icon(Icons.refresh))]),const SizedBox(height:14),Card(child:Padding(padding:const EdgeInsets.all(20),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[const Text('حالة السوق'),Text(m?['regime']?.toString()??'—',style:const TextStyle(fontSize:30,fontWeight:FontWeight.w900)),Text('العائد 20 جلسة: '+fmt(m?['return20'])+'%')] ))),const SizedBox(height:20),Row(children:[const Expanded(child:Text('أهم الفرص',style:TextStyle(fontSize:21,fontWeight:FontWeight.w900))),TextButton(onPressed:()=>widget.go(1),child:const Text('الكل'))]),...o.map((x)=>Opportunity(Map<String,dynamic>.from(x))),const SizedBox(height:10),Row(children:[Expanded(child:Act('تحليل سهم',Icons.search,()=>widget.go(2))),const SizedBox(width:10),Expanded(child:Act('المتابعة',Icons.star,()=>widget.go(3)))]) ]));}
class Opportunities extends StatefulWidget{const Opportunities({super.key});@override State<Opportunities>createState()=>_OState();}
class _OState extends State<Opportunities>{List<dynamic>r=[];@override void initState(){super.initState();load();}Future<void>load()async{try{final x=await Api.get('/opportunities?limit=40');if(mounted)setState(()=>r=x['data']??[]);}catch(_){}}@override Widget build(BuildContext c)=>RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.all(18),children:[const Text('الفرص',style:TextStyle(fontSize:29,fontWeight:FontWeight.w900)),const Text('شريعة فقط • ترتيب تنازلي • تشبع بيعي وارتداد وسوق وأخبار'),const SizedBox(height:16),...r.map((x)=>Opportunity(Map<String,dynamic>.from(x))) ]));}
class Opportunity extends StatelessWidget{final Map<String,dynamic>x;const Opportunity(this.x,{super.key});@override Widget build(BuildContext c)=>Card(child:ListTile(leading:CircleAvatar(child:Text(x['symbol'].toString()[0])),title:Text(x['symbol'].toString(),style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('RSI '+fmt(x['rsi14'])+' • ارتداد '+fmt(x['rebound_score'])+' • مخاطر '+fmt(x['risk_score'])),trailing:Text(fmt(x['opportunity_score']),style:TextStyle(fontWeight:FontWeight.w900,color:Theme.of(c).colorScheme.primary)),onTap:()=>Navigator.push(c,MaterialPageRoute(builder:(_)=>Details(symbol:x['symbol'].toString(),name:x['name']?.toString()??'')))));}
class Search extends StatefulWidget{const Search({super.key});@override State<Search>createState()=>_SState();}
class _SState extends State<Search>{final q=TextEditingController();List<dynamic>r=[];Future<void>s()async{try{final x=await Api.get('/stocks/search?q='+Uri.encodeQueryComponent(q.text));if(mounted)setState(()=>r=x['data']??[]);}catch(_){}}@override Widget build(BuildContext c)=>ListView(padding:const EdgeInsets.all(18),children:[const Text('تحليل سهم',style:TextStyle(fontSize:29,fontWeight:FontWeight.w900)),TextField(controller:q,onSubmitted:(_)=>s(),decoration:const InputDecoration(hintText:'رمز أو اسم الشركة',prefixIcon:Icon(Icons.search))),const SizedBox(height:10),FilledButton(onPressed:s,child:const Text('بحث')),...r.map((x)=>ListTile(title:Text(x['symbol'].toString()),subtitle:Text(x['name']?.toString()??''),onTap:()=>Navigator.push(c,MaterialPageRoute(builder:(_)=>Details(symbol:x['symbol'].toString(),name:x['name']?.toString()??'')))))]);}
class Details extends StatefulWidget{final String symbol,name;const Details({super.key,required this.symbol,required this.name});@override State<Details>createState()=>_DState();}
class _DState extends State<Details>{Map<String,dynamic>?d;String?ai;bool busy=false;@override void initState(){super.initState();load();}Future<void>load()async{try{final x=await Api.get('/stocks/'+widget.symbol+'/full-analysis');if(mounted)setState(()=>d=x);}catch(_){}}Future<void>watch()async{final p=await SharedPreferences.getInstance();final a=p.getStringList('watchlist')??[];if(!a.contains(widget.symbol))a.add(widget.symbol);await p.setStringList('watchlist',a);if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('تمت الإضافة للمتابعة')));}Future<void>run()async{setState(()=>busy=true);try{final x=await Api.post('/stocks/'+widget.symbol+'/ai-analysis');if(mounted)setState(()=>ai=x['text']?.toString());}catch(e){if(mounted)setState(()=>ai='تعذر تشغيل AI: '+e.toString());}finally{if(mounted)setState(()=>busy=false);}}@override Widget build(BuildContext c){if(d==null)return const Scaffold(body:Center(child:CircularProgressIndicator()));return Scaffold(appBar:AppBar(title:Text(widget.symbol)),body:RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.all(18),children:[Text(widget.name),Text(fmt(d!['close']),style:const TextStyle(fontSize:38,fontWeight:FontWeight.w900)),Text(fmt(d!['change_pct'])+'%',style:TextStyle(color:(numVal(d!['change_pct'])??0)>=0?Colors.green:Colors.red)),const SizedBox(height:8),FilledButton.icon(onPressed:watch,icon:const Icon(Icons.star_outline),label:const Text('إضافة لقائمة المتابعة')),Info('مؤشر الشريعة',Text(d!['sharia_compliant']==true?'متوافق مع المرجع الشرعي':'غير موجود في المرجع الشرعي؛ لا يدخل الفرص')),Info('خلاصة الفرصة',Column(children:[Row(children:[Stat('الفرصة',d!['final_opportunity_score']),Stat('الارتداد',d!['rebound_score']),Stat('المخاطر',d!['risk_score'])]),Text('السوق: '+(d!['market_regime']??'—').toString()+' • الأخبار: '+fmt(d!['news_score']))])),Info('المستويات',Wrap(spacing:16,runSpacing:12,children:[Stat('دعم',d!['support']),Stat('مقاومة',d!['resistance']),Stat('هدف1',d!['target1']),Stat('هدف2',d!['target2']),Stat('إيقاف',d!['stop']),Stat('R/R',d!['risk_reward'])])),
Info('الشارت',StockChart(points:((d!['chart'] as List?)??[]).map((e)=>numVal(e['close'])).whereType<double>().toList())),
Card(child:ExpansionTile(title:const Text('التفاصيل الفنية',style:TextStyle(fontWeight:FontWeight.w900)),children:[_row('RSI',d!['rsi14']),_row('SMA20',d!['sma20']),_row('SMA50',d!['sma50']),_row('SMA200',d!['sma200']),_row('ATR',d!['atr14']),_row('العائد20',d!['return20']),_row('العائد60',d!['return60']),_row('التذبذب',d!['volatility20']),_row('نسبة الحجم',d!['volume_ratio'])])),
Info('الأساسيات',Column(children:[_row('القطاع',d!['fundamentals']?['sector']),_row('P/E',d!['fundamentals']?['pe']),_row('EPS',d!['fundamentals']?['eps'])])),
Card(child:ExpansionTile(title:const Text('الأخبار',style:TextStyle(fontWeight:FontWeight.w900)),children:[...(d!['news'] as List? ?? []).take(6).map((n)=>ListTile(contentPadding:const EdgeInsets.symmetric(horizontal:16),title:Text(n['title']?.toString()??'',maxLines:2,overflow:TextOverflow.ellipsis),subtitle:Text((n['date']??'').toString()+' • '+fmt(n['polarity']))))])),
Info('AI',Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[if(ai!=null)Text(ai!),if(ai==null)const Text('شرح AI عند الطلب دون اختلاق أرقام أو إصدار أمر شراء/بيع.'),FilledButton(onPressed:busy?null:run,child:Text(busy?'جاري التحليل…':'تشغيل AI'))]))])));}
}
Widget _row(String a,d)=>ListTile(contentPadding:EdgeInsets.zero,title:Text(a),trailing:Text(fmt(d),style:const TextStyle(fontWeight:FontWeight.w800)));
class Watchlist extends StatefulWidget{const Watchlist({super.key});@override State<Watchlist>createState()=>_WState();}
class _WState extends State<Watchlist>{List<String>a=[];@override void initState(){super.initState();SharedPreferences.getInstance().then((p){if(mounted)setState(()=>a=p.getStringList('watchlist')??[]);});}Future<void>save()async{final p=await SharedPreferences.getInstance();await p.setStringList('watchlist',a);setState((){});}@override Widget build(BuildContext c)=>ListView(padding:const EdgeInsets.all(18),children:[const Text('المتابعة',style:TextStyle(fontSize:29,fontWeight:FontWeight.w900)),if(a.isEmpty)const Box('قائمة المتابعة فارغة.')else...a.map((s)=>ListTile(title:Text(s),trailing:IconButton(onPressed:(){a.remove(s);save();},icon:const Icon(Icons.delete_outline)),onTap:()=>Navigator.push(c,MaterialPageRoute(builder:(_)=>Details(symbol:s,name:s)))))]);}
class Portfolio extends StatefulWidget{const Portfolio({super.key});@override State<Portfolio>createState()=>_PState();}
class _PState extends State<Portfolio>{List<Map<String,dynamic>>a=[];Future<void>save()async{final p=await SharedPreferences.getInstance();await p.setString('portfolio',jsonEncode(a));if(mounted)setState((){});}Future<void>add()async{final s=TextEditingController(),q=TextEditingController(),v=TextEditingController();final ok=await showDialog<bool>(context:context,builder:(_)=>AlertDialog(title:const Text('إضافة مركز'),content:Column(mainAxisSize:MainAxisSize.min,children:[TextField(controller:s,decoration:const InputDecoration(labelText:'الرمز')),TextField(controller:q,keyboardType:TextInputType.number,decoration:const InputDecoration(labelText:'الكمية')),TextField(controller:v,keyboardType:TextInputType.number,decoration:const InputDecoration(labelText:'متوسط التكلفة'))]),actions:[TextButton(onPressed:()=>Navigator.pop(context),child:const Text('إلغاء')),FilledButton(onPressed:()=>Navigator.pop(context,true),child:const Text('حفظ'))]));if(ok==true&&s.text.trim().isNotEmpty){a.add({'symbol':s.text.trim().toUpperCase(),'qty':double.tryParse(q.text)??0,'avg':double.tryParse(v.text)??0});await save();}}@override void initState(){super.initState();SharedPreferences.getInstance().then((p){final x=p.getString('portfolio');if(x!=null&&mounted)setState(()=>a=(jsonDecode(x)as List).map((e)=>Map<String,dynamic>.from(e)).toList());});}@override Widget build(BuildContext c)=>ListView(padding:const EdgeInsets.all(18),children:[Row(children:[const Expanded(child:Text('المحفظة',style:TextStyle(fontSize:29,fontWeight:FontWeight.w900))),FilledButton.icon(onPressed:add,icon:const Icon(Icons.add),label:const Text('إضافة'))]),if(a.isEmpty)const Box('لم تضف مراكز بعد.')else...a.map((x)=>ListTile(title:Text(x['symbol'].toString()),subtitle:Text('كمية '+fmt(x['qty'])+' • تكلفة '+fmt(x['avg']))))]);}
class Info extends StatelessWidget{final String t;final Widget w;const Info(this.t,this.w,{super.key});@override Widget build(BuildContext c)=>Card(child:Padding(padding:const EdgeInsets.all(16),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(t,style:const TextStyle(fontWeight:FontWeight.w900,fontSize:17)),const SizedBox(height:10),w])));}
class Box extends StatelessWidget{final String t;const Box(this.t,{super.key});@override Widget build(BuildContext c)=>Info('معلومة',Text(t));}
class Stat extends StatelessWidget{final String t;final dynamic v;const Stat(this.t,this.v,{super.key});@override Widget build(BuildContext c)=>Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(t,style:const TextStyle(fontSize:10)),Text(fmt(v),style:const TextStyle(fontWeight:FontWeight.w900))]));}
class Act extends StatelessWidget{final String t;final IconData i;final VoidCallback f;const Act(this.t,this.i,this.f,{super.key});@override Widget build(BuildContext c)=>Card(child:InkWell(onTap:f,child:Padding(padding:const EdgeInsets.all(18),child:Row(children:[Icon(i,color:Theme.of(c).colorScheme.primary),const SizedBox(width:8),Text(t,style:const TextStyle(fontWeight:FontWeight.w800))]))));}
num?numVal(dynamic v)=>v is num?v.toDouble():double.tryParse(v?.toString()??'');
String fmt(dynamic v){final n=numVal(v);return n==null?'—':n.abs()>=1000?n.toStringAsFixed(0):n.toStringAsFixed(2);}

class StockChart extends StatelessWidget{
 final List<double> points;
 const StockChart({super.key,required this.points});
 @override Widget build(BuildContext c){
  if(points.length<2)return const SizedBox(height:120,child:Center(child:Text('لا توجد بيانات كافية للشارت')));
  return SizedBox(height:220,child:CustomPaint(painter:_ChartPainter(points,Theme.of(c).colorScheme.primary),child:const SizedBox.expand()));
 }
}
class _ChartPainter extends CustomPainter{
 final List<double> p; final Color color;
 _ChartPainter(this.p,this.color);
 @override void paint(Canvas canvas,Size size){
  final minV=p.reduce((a,b)=>a<b?a:b), maxV=p.reduce((a,b)=>a>b?a:b);
  final range=(maxV-minV).abs()<0.000001?1:(maxV-minV);
  final paint=Paint()..color=color..strokeWidth=3..style=PaintingStyle.stroke..strokeCap=StrokeCap.round;
  final path=Path();
  for(var i=0;i<p.length;i++){
   final x=size.width*(i/(p.length-1));
   final y=size.height-((p[i]-minV)/range)*(size.height-18)-9;
   if(i==0)path.moveTo(x,y);else path.lineTo(x,y);
  }
  canvas.drawPath(path,paint);
 }
 @override bool shouldRepaint(covariant _ChartPainter old)=>old.p!=p||old.color!=color;
}
class SettingsPage extends StatefulWidget{
 final Future<void>Function(bool)onTheme;
 const SettingsPage({super.key,required this.onTheme});
 @override State<SettingsPage>createState()=>_SettingsPageState();
}
class _SettingsPageState extends State<SettingsPage>{
 Map<String,dynamic>?h;
 @override void initState(){super.initState();load();}
 Future<void>load()async{try{final x=await Api.get('/health');if(mounted)setState(()=>h=Map<String,dynamic>.from(x));}catch(_){if(mounted)setState(()=>h={'error':'تعذر الاتصال بالواجهة الخلفية'});}}
 @override Widget build(BuildContext c)=>Scaffold(appBar:AppBar(title:const Text('الإعدادات')),body:ListView(padding:const EdgeInsets.all(18),children:[
  Card(child:SwitchListTile.adaptive(value:Theme.of(c).brightness==Brightness.dark,onChanged:widget.onTheme,title:const Text('الوضع الداكن'),secondary:const Icon(Icons.dark_mode_outlined))),
  Info('حالة البيانات',Column(children:[_row('EODHD',h?['eodhd_configured']==true?'متصل':'غير مهيأ'),_row('OANOR',h?['oanor_configured']==true?'متصل':'غير مهيأ'),_row('Gemini',h?['gemini_configured']==true?'متصل':'غير مهيأ')])),
  const Info('المرجعية الشرعية',Text('قائمة مرجعية مؤرخة وليست حكماً شرعياً دائماً. الفرص تُفلتر عليها فقط.')),
  const Info('التوقيت',Text('Africa/Cairo — يتعامل تلقائياً مع التوقيت الصيفي والشتوي.')),
 ]));
}

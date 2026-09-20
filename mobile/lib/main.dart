import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() => runApp(const MedhatStocksApp());

class MedhatStocksApp extends StatelessWidget {
  const MedhatStocksApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Medhat Stocks',
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0B0D12),
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF6C63FF), brightness: Brightness.dark),
        fontFamily: 'sans',
      ),
      home: const HomeShell(),
    );
  }
}

class Api {
  static const base = String.fromEnvironment('API_BASE', defaultValue: 'http://10.0.2.2:8000');
  static Future<Map<String,dynamic>> get(String path) async {
    final r = await http.get(Uri.parse('$base$path'));
    if (r.statusCode >= 400) throw Exception(jsonDecode(r.body)['detail'] ?? 'تعذر الاتصال');
    return jsonDecode(r.body) as Map<String,dynamic>;
  }
}

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});
  @override State<HomeShell> createState() => _HomeShellState();
}
class _HomeShellState extends State<HomeShell> {
  int tab = 0;
  final pages = const [Dashboard(), MarketPage(), SearchPage(), WatchlistPage(), PortfolioPage()];
  @override Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(child: pages[tab]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: tab,
        onDestinationSelected: (i)=>setState(()=>tab=i),
        backgroundColor: const Color(0xFF11141B),
        indicatorColor: const Color(0xFF292449),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'الرئيسية'),
          NavigationDestination(icon: Icon(Icons.show_chart), label: 'السوق'),
          NavigationDestination(icon: Icon(Icons.search), label: 'تحليل'),
          NavigationDestination(icon: Icon(Icons.star_border), selectedIcon: Icon(Icons.star), label: 'المتابعة'),
          NavigationDestination(icon: Icon(Icons.account_balance_wallet_outlined), label: 'المحفظة'),
        ],
      ),
    );
  }
}

class Dashboard extends StatelessWidget {
  const Dashboard({super.key});
  @override Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.fromLTRB(20, 18, 20, 28),
    children: [
      Row(children: [
        const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('مدحت ستوكس', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800)),
          SizedBox(height: 5), Text('EGX • تحليل ذكي', style: TextStyle(color: Colors.white54)),
        ])),
        CircleAvatar(backgroundColor: const Color(0xFF211E38), child: Icon(Icons.auto_graph, color: Colors.white)),
      ]),
      const SizedBox(height: 24),
      Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(borderRadius: BorderRadius.circular(24), gradient: const LinearGradient(colors:[Color(0xFF29234D),Color(0xFF171A27)])),
        child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('السوق المصري', style: TextStyle(color: Colors.white70)),
          SizedBox(height: 10), Text('حلّل السهم قبل القرار', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
          SizedBox(height: 8), Text('بيانات حقيقية • مؤشرات فنية • أساسيات • شرح بالذكاء الاصطناعي', style: TextStyle(color: Colors.white60)),
        ]),
      ),
      const SizedBox(height: 18),
      Row(children: [
        Expanded(child: _Action(icon: Icons.search, title:'ابحث عن سهم', onTap:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>const SearchPage())))),
        const SizedBox(width:12),
        Expanded(child: _Action(icon: Icons.bolt, title:'الفرص', onTap:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>const MarketPage())))),
      ]),
      const SizedBox(height: 24),
      const Text('ابدأ التحليل', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
      const SizedBox(height: 12),
      const StockCard(symbol:'COMI', name:'Commercial International Bank'),
    ],
  );
}

class _Action extends StatelessWidget {
  final IconData icon; final String title; final VoidCallback onTap;
  const _Action({required this.icon,required this.title,required this.onTap});
  @override Widget build(BuildContext context)=>InkWell(onTap:onTap,borderRadius:BorderRadius.circular(18),child:Container(padding:const EdgeInsets.symmetric(vertical:18,horizontal:14),decoration:BoxDecoration(color:const Color(0xFF151820),borderRadius:BorderRadius.circular(18),border:Border.all(color:Colors.white10)),child:Row(children:[Icon(icon,color:const Color(0xFF9C92FF)),const SizedBox(width:10),Expanded(child:Text(title,style:const TextStyle(fontWeight:FontWeight.w700)))])));
}

class StockCard extends StatefulWidget {
  final String symbol,name;
  const StockCard({super.key,required this.symbol,required this.name});
  @override State<StockCard> createState()=>_StockCardState();
}
class _StockCardState extends State<StockCard> {
  Map<String,dynamic>? data; String? error;
  @override void initState(){super.initState();load();}
  Future<void> load() async { try { final d=await Api.get('/stocks/${widget.symbol}/latest'); if(mounted)setState(()=>data=d); } catch(e){if(mounted)setState(()=>error=e.toString());}}
  @override Widget build(BuildContext context){
    final price=data?['close']; final ch=data?['change_pct'];
    return Card(color:const Color(0xFF151820),margin:EdgeInsets.zero,shape:RoundedRectangleBorder(borderRadius:BorderRadius.circular(20)),child:InkWell(
      onTap:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>StockDetails(symbol:widget.symbol,name:widget.name))),
      borderRadius:BorderRadius.circular(20),child:Padding(padding:const EdgeInsets.all(18),child:Row(children:[
        CircleAvatar(radius:25,backgroundColor:const Color(0xFF25213E),child:Text(widget.symbol[0],style:const TextStyle(fontWeight:FontWeight.bold))),
        const SizedBox(width:14),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(widget.symbol,style:const TextStyle(fontWeight:FontWeight.w800,fontSize:17)),Text(widget.name,overflow:TextOverflow.ellipsis,style:const TextStyle(color:Colors.white54))])),
        Column(crossAxisAlignment:CrossAxisAlignment.end,children:[Text(price==null?'—':price.toString(),style:const TextStyle(fontSize:18,fontWeight:FontWeight.w800)),Text(ch==null?'—':'${double.parse(ch.toString()).toStringAsFixed(2)}%',style:TextStyle(color:(ch??0)>=0?Colors.greenAccent:Colors.redAccent,fontWeight:FontWeight.w700))])
      ]))));
  }
}

class MarketPage extends StatelessWidget {
  const MarketPage({super.key});
  @override Widget build(BuildContext context)=>const _Page(title:'السوق',child:StockCard(symbol:'COMI',name:'Commercial International Bank'));
}
class WatchlistPage extends StatelessWidget {
  const WatchlistPage({super.key});
  @override Widget build(BuildContext context)=>const _Page(title:'المتابعة',child:Column(children:[Text('قائمة المتابعة محفوظة محليًا على الجهاز.'),SizedBox(height:16),StockCard(symbol:'COMI',name:'Commercial International Bank')]));
}
class PortfolioPage extends StatelessWidget {
  const PortfolioPage({super.key});
  @override Widget build(BuildContext context)=>const _Page(title:'المحفظة',child:Text('أضف الأسهم والكميات لمتابعة قيمة محفظتك.'));
}
class SearchPage extends StatefulWidget {
  const SearchPage({super.key});
  @override State<SearchPage> createState()=>_SearchPageState();
}
class _SearchPageState extends State<SearchPage>{
  final c=TextEditingController(); List<dynamic> results=[]; bool loading=false;
  Future<void> search() async {if(c.text.trim().isEmpty)return;setState(()=>loading=true);try{final d=await Api.get('/stocks/search?q=${Uri.encodeQueryComponent(c.text.trim())}');setState(()=>results=d['data']??[]);}catch(_){setState(()=>results=[]);}finally{if(mounted)setState(()=>loading=false);}}
  @override Widget build(BuildContext context)=>ListView(padding:const EdgeInsets.all(20),children:[
    const Text('تحليل سهم',style:TextStyle(fontSize:28,fontWeight:FontWeight.w800)),const SizedBox(height:18),
    TextField(controller:c,onSubmitted:(_)=>search(),decoration:InputDecoration(hintText:'ابحث بالرمز أو اسم الشركة',prefixIcon:const Icon(Icons.search),filled:true,fillColor:const Color(0xFF151820),border:OutlineInputBorder(borderRadius:BorderRadius.circular(18),borderSide:BorderSide.none))),
    const SizedBox(height:12),FilledButton.icon(onPressed:loading?null:search,icon:const Icon(Icons.search),label:const Text('بحث'),style:FilledButton.styleFrom(minimumSize:const Size.fromHeight(52),shape:RoundedRectangleBorder(borderRadius:BorderRadius.circular(16)))),
    const SizedBox(height:18),...results.map((x)=>ListTile(title:Text(x['symbol']??''),subtitle:Text(x['name']??''),onTap:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>StockDetails(symbol:x['symbol'],name:x['name'])))))
  ]);
}
class StockDetails extends StatefulWidget {final String symbol,name;const StockDetails({super.key,required this.symbol,required this.name});@override State<StockDetails> createState()=>_StockDetailsState();}
class _StockDetailsState extends State<StockDetails>{
 Map<String,dynamic>? a; Map<String,dynamic>? p; String? error;
 @override void initState(){super.initState();load();}
 Future<void> load() async {try{final vals=await Future.wait([Api.get('/stocks/${widget.symbol}/latest'),Api.get('/stocks/${widget.symbol}/analysis')]);if(mounted)setState(() { p = vals[0]; a = vals[1]; });}catch(e){if(mounted)setState(()=>error=e.toString());}}
 @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:Text(widget.symbol),backgroundColor:Colors.transparent),body:ListView(padding:const EdgeInsets.all(20),children:[
   Text(widget.name,style:const TextStyle(color:Colors.white54)),const SizedBox(height:18),
   Text(p?['close']?.toString()??'—',style:const TextStyle(fontSize:40,fontWeight:FontWeight.w900)),Text(p?['change_pct']==null?'—':'${double.parse(p!['change_pct'].toString()).toStringAsFixed(2)}%',style:TextStyle(color:(p?['change_pct']??0)>=0?Colors.greenAccent:Colors.redAccent,fontSize:18,fontWeight:FontWeight.bold)),
   const SizedBox(height:22),if(error!=null)Text(error!,style:const TextStyle(color:Colors.redAccent)),
   if(a!=null)...[_metric('الحالة',a!['status']),_metric('درجة الفرصة',a!['opportunity_score']),_metric('درجة المخاطر',a!['risk_score']),_metric('RSI 14',a!['rsi14']),_metric('دعم',a!['support']),_metric('مقاومة',a!['resistance'])],
 ]));
}
Widget _metric(String k,d)=>Card(color:const Color(0xFF151820),child:ListTile(title:Text(k),trailing:Text(d?.toString()??'—',style:const TextStyle(fontWeight:FontWeight.w800))));
class _Page extends StatelessWidget{final String title;final Widget child;const _Page({required this.title,required this.child});@override Widget build(BuildContext context)=>ListView(padding:const EdgeInsets.all(20),children:[Text(title,style:const TextStyle(fontSize:28,fontWeight:FontWeight.w800)),const SizedBox(height:18),child]);}

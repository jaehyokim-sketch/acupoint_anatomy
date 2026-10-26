#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Acupoint Anatomy & Substrate Identification — 원격 stdio MCP 서버 (GitHub 스트리밍)

로컬 저장소 없이 이 파일 하나로 GitHub 저장소의 데이터를 받아 쓴다. 도구는 로컬 server.py와 같다.

  python remote_server.py [--repo <owner>/<repo>] [--branch main] [--token <PAT>] [--cache-dir <경로>] [--ttl 3600]
  환경변수: GITHUB_REPO · GITHUB_BRANCH · GITHUB_TOKEN · ACUPOINT_CACHE_DIR

데이터 갱신 방식
  - 원전 목록·변경은 data/classics/index.json(파일별 SHA-1)으로 확인한다 → GitHub API 호출 횟수 제한(시간당 60회)과 무관
    (index.json이 없을 때만 GitHub Contents API로 목록을 받는다)
  - 원전 파일은 SHA-1을 이름으로 디스크 캐시(~/.acupoint_anatomy/cache/classics)에 저장해 재시작 후에도 다시 받지 않는다
  - index.json과 그 밖의 데이터는 --ttl(기본 3600초)마다 다시 확인하므로, 저장소가 갱신되면 재시작 없이 반영된다
  - 보조 문헌(동의보감 등)과 FMA 로컬 색인은 원격 모드에서 쓰지 않는다(FMA는 대응표 JSON으로 응답)
"""
# ================================================================================================
# 자동 생성 파일 — 직접 고치지 마세요.
#   원본: mcp_server/acupoint_core.py(도구 로직) + mcp_server/remote_backend.py(GitHub 백엔드)
#   생성: python scripts/build_remote_server.py
# ================================================================================================

# ----- acupoint_core.py -----
"""
acupoint_core.py — [경혈해부] MCP 서버 공통 로직 (로컬 server.py · 원격 remote_server.py 공용)

데이터를 어디서 읽는지(로컬 디스크 / GitHub)는 백엔드 객체가 맡고, 이 모듈은 도구 정의·검색·채점 로직만 갖는다.
remote_server.py는 scripts/build_remote_server.py가 이 파일과 remote_backend.py를 합쳐 만든다(단일 파일 배포).

백엔드가 제공해야 하는 것
  label                       : 데이터 출처 표기 (예: "로컬 C:/workspace/acupoint_anatomy")
  read_text(key) -> str       : framework, layer_b_json, layer_b_md, master_csv, biomed_json, fma_json, reference_json
  classics_books() -> list    : [(필터 키, 디렉토리 식별자, 표기, 종류 "core"|"extra")]
  classics_list(dir_id) -> list[str]
  classics_read(dir_id, name) -> str
  classics_prefetch(dir_id, names)   : 여러 파일을 미리 읽어 둘 때(원격 병렬 다운로드). 로컬은 아무것도 안 해도 된다
  (선택) classics_version(dir_id, name) : 파일 버전(SHA 등). 바뀌면 행 캐시를 새로 만든다
  (선택) cache_token()        : 값이 바뀌면 파싱해 둔 데이터를 버린다(원격 TTL)
  fma_instance() -> (FMA 객체, fma_query 모듈) 또는 (None, None)

도구 7종
  get_acupoint_anatomy_profile · get_fma_anatomy_profile · search_biomedical_reflex_db · get_layer_b_registry
  calculate_ari_v3_score · search_classic_records · get_framework_protocol
"""
import csv
import io
import json
import re
import sys

SERVER_NAME = "acupoint-anatomy-mcp"
SERVER_VERSION = "3.0.0"
PROTOCOL_VERSION = "2024-11-05"
SUPPORTED_PROTOCOLS = ("2024-11-05", "2025-03-26", "2025-06-18")

BACKEND = None
_CACHE = {}


def set_backend(backend):
    global BACKEND
    BACKEND = backend
    _CACHE.clear()


def _cached(key, loader):
    if key not in _CACHE:
        _CACHE[key] = loader()
    return _CACHE[key]


# ---------------------------------------------------------------------------
# 번체·간체·이체자 정규화
# ---------------------------------------------------------------------------
# 번체→간체 단일 글자 대응 4,105쌍: OpenCC 'TSCharacters.txt'(Apache License 2.0)에서 첫 후보만 추린 것.
# OpenCC가 설치되어 있으면 검색어에는 OpenCC(구 단위 변환)를 먼저 적용하고, 코퍼스 행에는 빠른 표 변환만 쓴다.
_T2S_PAIRS = (
    "㑮𫝈㑯㑔㑳㑇㑶㐹㒓𠉂㓄𪠟㓨刾㔋𪟎㖮𪠵㗲𠵾㗿𪡛㘉𠰱㘓𪢌㘔𫬐㘚㘎㛝𫝦㜄㚯㜏㛣㜐𫝧㜗𡞋㜢𡞱㜷𡝠㞞𪨊㟺𪩇㠏㟆㠣𫵷㢗𪪑㢝𢋈㥮㤘㦎𢛯㦛𢗓㦞𪫷㨻𪮃㩋𪮋㩜㨫㩳㧐㩵擜㪎𪯋㯤𣘐㰙𣗙"
    "㵗𣳆㵾𪷍㶆𫞛㷍𤆢㷿𤈷㸇𤎺㹽𫞣㺏𤠋㺜𪺻㻶𪼋㿖𪽮㿗𤻊㿧𤽯䀉𥁢䀹𥅴䁪𥇢䁻䀥䂎𥎝䃮鿎䅐𫀨䅳𫀬䆉𫁂䉑𫁲䉙𥬀䉬𫂈䉲𥮜䉶𫁷䊭𥺅䊷䌶䊺𫄚䋃𫄜䋔𫄞䋙䌺䋚䌻䋦𫄩䋹䌿䋻䌾䋼𫄮䋿𦈓䌈𦈖"
    "䌋𦈘䌖𦈜䌝𦈟䌟𦈞䌥𦈠䌰𦈙䍤𫅅䍦䍠䍽𦍠䎙𫅭䎱䎬䓣𬜯䕤𫟕䕳𦰴䖅𫟑䗅𫊪䗿𧉞䙔𫋲䙡䙌䙱𧜭䚩𫌯䛄𫍠䛳𫍫䜀䜧䜖𫟢䝭𫎧䝻𧹕䝼䞍䞈𧹑䞋𫎪䞓𫎭䟃𫎺䟆𫎳䟐𫎱䠆𫏃䠱𨅛䡐𫟤䡩𫟥䡵𫟦䢨𨑹"
    "䤤𫟺䥄𫠀䥇䦂䥑鿏䥕𬭯䥗𫔋䥩𨱖䥯𫔆䥱䥾䦘𨸄䦛䦶䦟䦷䦯𫔵䦳𨷿䧢𨸟䪊𫖅䪏𩏼䪗𩐀䪘𩏿䪴𫖫䪾𫖬䫀𫖱䫂𫖰䫟𫖲䫴𩖗䫶𫖺䫻𫗇䫾𫠈䬓𫗊䬘𩙮䬝𩙯䬞𩙧䬧𫗟䭀𩠇䭃𩠈䭑𫗱䭔𫗰䭿𩧭䮄𫠊䮝𩧰"
    "䮞𩨁䮠𩧿䮫𩨇䮰𫘮䮳𩨏䮾𩧪䯀䯅䯤𩩈䰾鲃䱀𫚐䱁𫚏䱙𩾈䱧𫚠䱬𩾊䱰𩾋䱷䲣䱸𫠑䱽䲝䲁鳚䲅𫚜䲖𩾂䲘鳤䲰𪉂䳜𫛬䳢𫛰䳤𫛮䳧𫛺䳫𫛼䴉鹮䴋𫜅䴬𪎈䴱𫜒䴴𪎋䴽𫜔䵳𪑅䵴𫜙䶕𫜨䶲𫜳丟丢並并"
    "乾干亂乱亙亘亞亚佇伫佈布佔占併并來来侖仑侶侣侷局俁俣係系俓𠇹俔伣俠侠俥伡俬私倀伥倆俩倈俫倉仓個个們们倖幸倫伦倲㑈偉伟偑㐽側侧偵侦偽伪傌㐷傑杰傖伧傘伞備备傢家傭佣"
    "傯偬傳传傴伛債债傷伤傾倾僂偻僅仅僉佥僑侨僕仆僞伪僤𫢸僥侥僨偾僱雇價价儀仪儁俊儂侬億亿儈侩儉俭儎傤儐傧儔俦儕侪儘尽償偿儣𠆲優优儭𠋆儲储儷俪儸㑩儺傩儻傥儼俨兇凶兌兑"
    "兒儿兗兖內内兩两冊册冑胄冪幂凈净凍冻凙𪞝凜凛凱凯別别刪删剄刭則则剋克剎刹剗刬剛刚剝剥剮剐剴剀創创剷铲剾𠛅劃划劇剧劉刘劊刽劌刿劍剑劏㓥劑剂劚㔉勁劲勑𠡠動动務务勛勋"
    "勝胜勞劳勢势勣𪟝勩勚勱劢勳勋勵励勸劝勻匀匭匦匯汇匱匮區区協协卹恤卻却卽即厙厍厠厕厤历厭厌厲厉厴厣參参叄叁叢丛吒咤吳吴吶呐呂吕咼呙員员哯𠯟唄呗唓𪠳唸念問问啓启啞哑"
    "啟启啢唡喎㖞喚唤喪丧喫吃喬乔單单喲哟嗆呛嗇啬嗊唝嗎吗嗚呜嗩唢嗰𠮶嗶哔嗹𪡏嘆叹嘍喽嘓啯嘔呕嘖啧嘗尝嘜唛嘩哗嘪𪡃嘮唠嘯啸嘰叽嘳𪡞嘵哓嘸呒嘺𪡀嘽啴噁恶噅𠯠噓嘘噚㖊噝咝"
    "噞𪡋噠哒噥哝噦哕噯嗳噲哙噴喷噸吨噹当嚀咛嚇吓嚌哜嚐尝嚕噜嚙啮嚛𪠸嚥咽嚦呖嚧𠰷嚨咙嚮向嚲亸嚳喾嚴严嚶嘤嚽𪢕囀啭囁嗫囂嚣囃𠱞囅冁囈呓囉啰囌苏囑嘱囒𪢠囪囱圇囵國国圍围"
    "園园圓圆圖图團团圞𪢮垻坝埡垭埨𫭢埬𪣆埰采執执堅坚堊垩堖垴堚𪣒堝埚堯尧報报場场塊块塋茔塏垲塒埘塗涂塚冢塢坞塤埙塵尘塸𫭟塹堑塿𪣻墊垫墜坠墠𫮃墮堕墰坛墲𪢸墳坟墶垯墻墙"
    "墾垦壇坛壈𡒄壋垱壎埙壓压壗𡋤壘垒壙圹壚垆壜坛壞坏壟垄壠垅壢坜壣𪤚壩坝壪塆壯壮壺壶壼壸壽寿夠够夢梦夥伙夾夹奐奂奧奥奩奁奪夺奬奖奮奋奼姹妝妆姍姗姦奸娙𫰛娛娱婁娄婡𫝫"
    "婦妇婭娅媈𫝨媧娲媯妫媰㛀媼媪媽妈嫋袅嫗妪嫵妩嫺娴嫻娴嫿婳嬀妫嬃媭嬇𫝬嬈娆嬋婵嬌娇嬙嫱嬡嫒嬣𪥰嬤嬷嬦𫝩嬪嫔嬰婴嬸婶嬻𪥿孃娘孄𫝮孆𫝭孇𪥫孋㛤孌娈孎𡠟孫孙學学孻𡥧孾𪧀"
    "孿孪宮宫寀采寠𪧘寢寝實实寧宁審审寫写寬宽寵宠寶宝將将專专尋寻對对導导尷尴屆届屍尸屓屃屜屉屢屡層层屨屦屩𪨗屬属岡冈峯峰峴岘島岛峽峡崍崃崑昆崗岗崙仑崢峥崬岽嵐岚嵗岁"
    "嵼𡶴嵽𫶇嵾㟥嶁嵝嶄崭嶇岖嶈𡺃嶔嵚嶗崂嶘𡺄嶠峤嶢峣嶧峄嶨峃嶮崄嶸嵘嶹𫝵嶺岭嶼屿嶽岳巊𪩎巋岿巒峦巔巅巖岩巗𪨷巘𪩘巰巯巹卺帥帅師师帳帐帶带幀帧幃帏幓㡎幗帼幘帻幝𪩷幟帜"
    "幣币幩𪩸幫帮幬帱幹干幾几庫库廁厕廂厢廄厩廈厦廎庼廕荫廚厨廝厮廞𫷷廟庙廠厂廡庑廢废廣广廧𪪞廩廪廬庐廳厅弒弑弔吊弳弪張张強强彃𪪼彄𫸩彆别彈弹彌弥彎弯彔录彙汇彠彟彥彦"
    "彫雕彲彨彿佛後后徑径從从徠徕復复徵征徹彻徿𪫌恆恒恥耻悅悦悞悮悵怅悶闷悽凄惡恶惱恼惲恽惻恻愛爱愜惬愨悫愴怆愷恺愻𢙏愾忾慄栗態态慍愠慘惨慚惭慟恸慣惯慤悫慪怄慫怂慮虑"
    "慳悭慶庆慺㥪慼戚慾欲憂忧憊惫憐怜憑凭憒愦憖慭憚惮憢𢙒憤愤憫悯憮怃憲宪憶忆憸𪫺憹𢙐懀𢙓懇恳應应懌怿懍懔懎𢠁懞蒙懟怼懣懑懤㤽懨恹懲惩懶懒懷怀懸悬懺忏懼惧懾慑戀恋戇戆"
    "戔戋戧戗戩戬戰战戱戯戲戏戶户拋抛挩捝挱挲挾挟捨舍捫扪捱挨捲卷掃扫掄抡掆㧏掗挜掙挣掚𪭵掛挂採采揀拣揚扬換换揮挥揯搄損损搖摇搗捣搵揾搶抢摋𢫬摐𪭢摑掴摜掼摟搂摯挚摳抠"
    "摶抟摺折摻掺撈捞撊𪭾撏挦撐撑撓挠撝㧑撟挢撣掸撥拨撧𪮖撫抚撲扑撳揿撻挞撾挝撿捡擁拥擄掳擇择擊击擋挡擓㧟擔担據据擟𪭧擠挤擣捣擫𢬍擬拟擯摈擰拧擱搁擲掷擴扩擷撷擺摆擻擞"
    "擼撸擽㧰擾扰攄摅攆撵攋𪮶攏拢攔拦攖撄攙搀攛撺攜携攝摄攢攒攣挛攤摊攪搅攬揽敎教敓敚敗败敘叙敵敌數数斂敛斃毙斅𢽾斆敩斕斓斬斩斷断斸𣃁於于旂旗旣既昇升時时晉晋晛𬀪晝昼"
    "暈晕暉晖暐𬀩暘旸暢畅暫暂曄晔曆历曇昙曉晓曊𪰶曏向曖暧曠旷曥𣆐曨昽曬晒書书會会朥𦛨朧胧朮术東东枴拐柵栅柺拐査查桱𣐕桿杆梔栀梖𪱷梘枧梜𬂩條条梟枭梲棁棄弃棊棋棖枨棗枣"
    "棟栋棡㭎棧栈棲栖棶梾椏桠椲㭏楇𣒌楊杨楓枫楨桢業业極极榘矩榦干榪杩榮荣榲榅榿桤構构槍枪槓杠槤梿槧椠槨椁槫𣏢槮椮槳桨槶椢槼椝樁桩樂乐樅枞樑梁樓楼標标樞枢樠𣗊樢㭤樣样"
    "樤𣔌樧榝樫㭴樳桪樸朴樹树樺桦樿椫橈桡橋桥機机橢椭橫横橯𣓿檁檩檉柽檔档檜桧檟槚檢检檣樯檭𣘴檮梼檯台檳槟檵𪲛檸柠檻槛櫃柜櫅𪲎櫍𬃊櫓橹櫚榈櫛栉櫝椟櫞橼櫟栎櫠𪲮櫥橱櫧槠"
    "櫨栌櫪枥櫫橥櫬榇櫱蘖櫳栊櫸榉櫻樱欄栏欅榉欇𪳍權权欍𣐤欏椤欐𪲔欑𪴙欒栾欓𣗋欖榄欘𣚚欞棂欽钦歎叹歐欧歟欤歡欢歲岁歷历歸归歿殁殘残殞殒殢𣨼殤殇殨㱮殫殚殭僵殮殓殯殡殰㱩"
    "殲歼殺杀殻壳殼壳毀毁毆殴毊𪵑毿毵氂牦氈毡氌氇氣气氫氢氬氩氭𣱝氳氲氾泛汎泛汙污決决沒没沖冲況况泝溯洩泄洶汹浹浃浿𬇙涇泾涗涚涼凉淒凄淚泪淥渌淨净淩凌淪沦淵渊淶涞淺浅"
    "渙涣減减渢沨渦涡測测渾浑湊凑湋𣲗湞浈湧涌湯汤溈沩準准溝沟溡𪶄溫温溮浉溳涢溼湿滄沧滅灭滌涤滎荥滙汇滬沪滯滞滲渗滷卤滸浒滻浐滾滚滿满漁渔漊溇漍𬇹漚沤漢汉漣涟漬渍漲涨"
    "漵溆漸渐漿浆潁颍潑泼潔洁潕𣲘潙沩潚㴋潛潜潣𫞗潤润潯浔潰溃潷滗潿涠澀涩澅𣶩澆浇澇涝澐沄澗涧澠渑澤泽澦滪澩泶澫𬇕澬𫞚澮浍澱淀澾㳠濁浊濃浓濄㳡濆𣸣濕湿濘泞濚溁濛蒙濜浕"
    "濟济濤涛濧㳔濫滥濰潍濱滨濺溅濼泺濾滤濿𪵱瀂澛瀃𣽷瀅滢瀆渎瀇㲿瀉泻瀋沈瀏浏瀕濒瀘泸瀝沥瀟潇瀠潆瀦潴瀧泷瀨濑瀰弥瀲潋瀾澜灃沣灄滠灍𫞝灑洒灒𪷽灕漓灘滩灙𣺼灝灏灡㳕灣湾"
    "灤滦灧滟灩滟災灾為为烏乌烴烃無无煇𪸩煉炼煒炜煙烟煢茕煥焕煩烦煬炀煱㶽熂𪸕熅煴熉𤈶熌𤇄熒荧熓𤆡熗炝熚𤇹熡𤋏熰𬉼熱热熲颎熾炽燀𬊤燁烨燈灯燉炖燒烧燖𬊈燙烫燜焖營营燦灿"
    "燬毁燭烛燴烩燶㶶燻熏燼烬燾焘爃𫞡爄𤇃爇𦶟爍烁爐炉爖𤇭爛烂爥𪹳爧𫞠爭争爲为爺爷爾尔牀床牆墙牘牍牽牵犖荦犛牦犞𪺭犢犊犧牺狀状狹狭狽狈猌𪺽猙狰猶犹猻狲獁犸獃呆獄狱獅狮"
    "獊𪺷獎奖獨独獩𤞃獪狯獫猃獮狝獰狞獱㺍獲获獵猎獷犷獸兽獺獭獻献獼猕玀猡玁𤞤珼𫞥現现琱雕琺珐琿珲瑋玮瑒玚瑣琐瑤瑶瑩莹瑪玛瑲玱瑻𪻲瑽𪻐璉琏璊𫞩璕𬍤璗𬍡璝𪻺璡琎璣玑璦瑷"
    "璫珰璯㻅環环璵玙璸瑸璼𫞨璽玺璾𫞦璿璇瓄𪻨瓅𬍛瓊琼瓏珑瓔璎瓕𤦀瓚瓒瓛𤩽甌瓯甕瓮產产産产甦苏甯宁畝亩畢毕畫画異异畵画當当畼𪽈疇畴疊叠痙痉痠酸痮𪽪痾疴瘂痖瘋疯瘍疡瘓痪"
    "瘞瘗瘡疮瘧疟瘮瘆瘱𪽷瘲疭瘺瘘瘻瘘療疗癆痨癇痫癉瘅癐𤶊癒愈癘疠癟瘪癡痴癢痒癤疖癥症癧疬癩癞癬癣癭瘿癮瘾癰痈癱瘫癲癫發发皁皂皚皑皟𤾀皰疱皸皲皺皱盃杯盜盗盞盏盡尽監监"
    "盤盘盧卢盨𪾔盪荡眝𪾣眞真眥眦眾众睍𪾢睏困睜睁睞睐瞘眍瞜䁖瞞瞒瞤𥆧瞶瞆瞼睑矇蒙矉𪾸矑𪾦矓眬矚瞩矯矫硃朱硜硁硤硖硨砗硯砚碕埼碙𥐻碩硕碭砀碸砜確确碼码碽䂵磑硙磚砖磠硵"
    "磣碜磧碛磯矶磽硗磾䃅礄硚礆硷礎础礐𬒈礒𥐟礙碍礦矿礪砺礫砾礬矾礮𪿫礱砻祕秘祿禄禍祸禎祯禕祎禡祃禦御禪禅禮礼禰祢禱祷禿秃秈籼稅税稈秆稏䅉稜棱稟禀種种稱称穀谷穇䅟穌稣"
    "積积穎颖穠秾穡穑穢秽穩稳穫获穭穞窩窝窪洼窮穷窯窑窵窎窶窭窺窥竄窜竅窍竇窦竈灶竊窃竚𥩟竪竖竱𫁟競竞筆笔筍笋筧笕筴䇲箇个箋笺箏筝節节範范築筑篋箧篔筼篘𥬠篠筿篢𬕂篤笃"
    "篩筛篳筚篸𥮾簀箦簂𫂆簍篓簑蓑簞箪簡简簢𫂃簣篑簫箫簹筜簽签簾帘籃篮籅𥫣籋𥬞籌筹籔䉤籙箓籛篯籜箨籟籁籠笼籤签籩笾籪簖籬篱籮箩籲吁粵粤糉粽糝糁糞粪糧粮糰团糲粝糴籴糶粜"
    "糹纟糺𫄙糾纠紀纪紂纣紃𬘓約约紅红紆纡紇纥紈纨紉纫紋纹納纳紐纽紓纾純纯紕纰紖纼紗纱紘纮紙纸級级紛纷紜纭紝纴紞𬘘紟𫄛紡纺紬䌷紮扎細细紱绂紲绁紳绅紵纻紹绍紺绀紼绋紿绐"
    "絀绌絁𫄟終终絃弦組组絅䌹絆绊絍𫟃絎绗結结絕绝絙𫄠絛绦絝绔絞绞絡络絢绚絥𫄢給给絧𫄡絨绒絪𬘡絰绖統统絲丝絳绛絶绝絹绢絺𫄨綀𦈌綁绑綃绡綄𬘫綆绠綇𦈋綈绨綉绣綋𫟄綌绤綎𬘩"
    "綏绥綐䌼綑捆經经綖𫄧綜综綝𬘭綞缍綟𫄫綠绿綡𫟅綢绸綣绻綧𬘯綪𬘬綫线綬绶維维綯绹綰绾綱纲網网綳绷綴缀綵彩綸纶綹绺綺绮綻绽綽绰綾绫綿绵緄绲緇缁緊紧緋绯緍𦈏緑绿緒绪緓绬"
    "緔绱緗缃緘缄緙缂線线緝缉緞缎緟𫟆締缔緡缗緣缘緤𫄬緦缌編编緩缓緬缅緮𫄭緯纬緰𦈕緱缑緲缈練练緶缏緷𦈉緸𦈑緹缇緻致緼缊縈萦縉缙縊缢縋缒縍𫄰縎𦈔縐绉縑缣縕缊縗缞縛缚縝缜"
    "縞缟縟缛縣县縧绦縫缝縬𦈚縭缡縮缩縯𬙂縰𫄳縱纵縲缧縳䌸縴纤縵缦縶絷縷缕縸𫄲縹缥縺𦈐總总績绩繂𫄴繃绷繅缫繆缪繈𫄶繏𦈝繐𰬸繒缯繓𦈛織织繕缮繚缭繞绕繟𦈎繡绣繢缋繨𫄤繩绳"
    "繪绘繫系繬𫄱繭茧繮缰繯缳繰缲繳缴繶𫄷繷𫄣繸䍁繹绎繻𦈡繼继繽缤繾缱繿䍀纁𫄸纆𬙊纇颣纈缬纊纩續续纍累纏缠纓缨纔才纕𬙋纖纤纗𫄹纘缵纚𫄥纜缆缽钵罃䓨罈坛罌罂罎坛罰罚罵骂"
    "罷罢羅罗羆罴羈羁羋芈羣群羥羟羨羡義义羵𫅗羶膻習习翫玩翬翚翹翘翽翙耬耧耮耢聖圣聞闻聯联聰聪聲声聳耸聵聩聶聂職职聹聍聻𫆏聽听聾聋肅肃脅胁脈脉脛胫脣唇脥𣍰脩修脫脱脹胀"
    "腎肾腖胨腡脶腦脑腪𣍯腫肿腳脚腸肠膃腽膕腘膚肤膞䏝膠胶膢𦝼膩腻膹𪱥膽胆膾脍膿脓臉脸臍脐臏膑臗𣎑臘腊臚胪臟脏臠脔臢臜臥卧臨临臺台與与興兴舉举舊旧舘馆艙舱艣𫇛艤舣艦舰"
    "艫舻艱艰艷艳芻刍苧苎茲兹荊荆莊庄莖茎莢荚莧苋菕𰰨華华菴庵菸烟萇苌萊莱萬万萴荝萵莴葉叶葒荭葝𫈎葤荮葦苇葯药葷荤蒍𫇭蒐搜蒓莼蒔莳蒕蒀蒞莅蒭𫇴蒼苍蓀荪蓆席蓋盖蓧𦰏蓮莲"
    "蓯苁蓴莼蓽荜蔄𬜬蔔卜蔘参蔞蒌蔣蒋蔥葱蔦茑蔭荫蔯𫈟蔿𫇭蕁荨蕆蒇蕎荞蕒荬蕓芸蕕莸蕘荛蕝𫈵蕢蒉蕩荡蕪芜蕭萧蕳𫈉蕷蓣蕽𫇽薀蕰薆𫉁薈荟薊蓟薌芗薑姜薔蔷薘荙薟莶薦荐薩萨薳䓕"
    "薴苧薵䓓薹苔薺荠藍蓝藎荩藝艺藥药藪薮藭䓖藴蕴藶苈藷𫉄藹蔼藺蔺蘀萚蘄蕲蘆芦蘇苏蘊蕴蘋苹蘚藓蘞蔹蘟𦻕蘢茏蘭兰蘺蓠蘿萝虆蔂虉𬟁處处虛虚虜虏號号虧亏虯虬蛺蛱蛻蜕蜆蚬蝀𬟽"
    "蝕蚀蝟猬蝦虾蝨虱蝸蜗螄蛳螞蚂螢萤螮䗖螻蝼螿螀蟂𫋇蟄蛰蟈蝈蟎螨蟘𫋌蟜𫊸蟣虮蟬蝉蟯蛲蟲虫蟳𫊻蟶蛏蟻蚁蠀𧏗蠁蚃蠅蝇蠆虿蠍蝎蠐蛴蠑蝾蠔蚝蠙𧏖蠟蜡蠣蛎蠦𫊮蠨蟏蠱蛊蠶蚕蠻蛮"
    "蠾𧑏衆众衊蔑術术衕同衚胡衛卫衝冲袞衮裊袅裏里補补裝装裡里製制複复褌裈褘袆褲裤褳裢褸褛褻亵襀𫌀襇裥襉裥襏袯襓𫋹襖袄襗𫋷襘𫋻襝裣襠裆襤褴襪袜襬摆襯衬襰𧝝襲袭襴襕襵𫌇"
    "覈核見见覎觃規规覓觅視视覘觇覛𫌪覡觋覥觍覦觎親亲覬觊覯觏覲觐覷觑覹𫌭覺觉覼𫌨覽览覿觌觀观觴觞觶觯觸触訁讠訂订訃讣計计訊讯訌讧討讨訏𬣙訐讦訑𫍙訒讱訓训訕讪訖讫託托"
    "記记訛讹訜𫍛訝讶訞𫍚訟讼訢䜣訣诀訥讷訨𫟞訩讻訪访設设許许訴诉訶诃診诊註注証证詀𧮪詁诂詆诋詊𫟟詎讵詐诈詑𫍡詒诒詓𫍜詔诏評评詖诐詗诇詘诎詛诅詝𬣞詞词詠咏詡诩詢询詣诣"
    "試试詩诗詪𬣳詫诧詬诟詭诡詮诠詰诘話话該该詳详詵诜詷𫍣詼诙詿诖誂𫍥誄诔誅诛誆诓誇夸誋𫍪誌志認认誑诳誒诶誕诞誘诱誚诮語语誠诚誡诫誣诬誤误誥诰誦诵誨诲說说誫𫍨説说誰谁"
    "課课誳𫍮誴𫟡誶谇誷𫍬誹诽誺𫍧誼谊誾訚調调諂谄諄谆談谈諉诿請请諍诤諏诹諑诼諒谅諓𬣡論论諗谂諛谀諜谍諝谞諞谝諟𬤊諡谥諢诨諣𫍩諤谔諥𫍳諦谛諧谐諫谏諭谕諮咨諯𫍱諰𫍰諱讳"
    "諲𬤇諳谙諴𫍯諶谌諷讽諸诸諺谚諼谖諾诺謀谋謁谒謂谓謄誊謅诌謆𫍸謉𫍷謊谎謎谜謏𫍲謐谧謔谑謖谡謗谤謙谦謚谥講讲謝谢謠谣謡谣謨谟謫谪謬谬謭谫謯𫍹謱𫍴謳讴謸𫍵謹谨謾谩譁哗"
    "譂𫟠譅𰶎譆𫍻證证譊𫍢譎谲譏讥譑𫍤譓𬤝譖谮識识譙谯譚谭譜谱譞𫍽譟噪譨𫍦譫谵譭毁譯译議议譴谴護护譸诪譽誉譾谫讀读讅谉變变讋詟讌䜩讎雠讒谗讓让讕谰讖谶讚赞讜谠讞谳豈岂"
    "豎竖豐丰豔艳豬猪豵𫎆豶豮貓猫貗𫎌貙䝙貝贝貞贞貟贠負负財财貢贡貧贫貨货販贩貪贪貫贯責责貯贮貰贳貲赀貳贰貴贵貶贬買买貸贷貺贶費费貼贴貽贻貿贸賀贺賁贲賂赂賃赁賄贿賅赅"
    "資资賈贾賊贼賑赈賒赊賓宾賕赇賙赒賚赉賜赐賝𫎩賞赏賟𧹖賠赔賡赓賢贤賣卖賤贱賦赋賧赕質质賫赍賬账賭赌賰䞐賴赖賵赗賺赚賻赙購购賽赛賾赜贃𧹗贄贽贅赘贇赟贈赠贉𫎫贊赞贋赝"
    "贍赡贏赢贐赆贑𫎬贓赃贔赑贖赎贗赝贚𫎦贛赣贜赃赬赪趕赶趙赵趨趋趲趱跡迹踐践踰逾踴踊蹌跄蹔𫏐蹕跸蹟迹蹠跖蹣蹒蹤踪蹳𫏆蹺跷蹻𫏋躂跶躉趸躊踌躋跻躍跃躎䟢躑踯躒跞躓踬躕蹰"
    "躘𨀁躚跹躝𨅬躡蹑躥蹿躦躜躪躏軀躯軉𨉗車车軋轧軌轨軍军軏𫐄軑轪軒轩軔轫軕𫐅軗𨐅軛轭軜𫐇軝𬨂軟软軤轷軨𫐉軫轸軬𫐊軲轱軷𫐈軸轴軹轵軺轺軻轲軼轶軾轼軿𫐌較较輄𨐈輅辂輇辁"
    "輈辀載载輊轾輋𪨶輒辄輓挽輔辅輕轻輖𫐏輗𫐐輛辆輜辎輝辉輞辋輟辍輢𫐎輥辊輦辇輨𫐑輩辈輪轮輬辌輮𫐓輯辑輳辏輶𬨎輷𫐒輸输輻辐輼辒輾辗輿舆轀辒轂毂轄辖轅辕轆辘轇𫐖轉转轊𫐕"
    "轍辙轎轿轐𫐗轔辚轗𫐘轟轰轠𫐙轡辔轢轹轣𫐆轤轳辦办辭辞辮辫辯辩農农迴回逕迳這这連连週周進进遊游運运過过達达違违遙遥遜逊遞递遠远遡溯適适遱𫐷遲迟遷迁選选遺遗遼辽邁迈"
    "還还邇迩邊边邏逻邐逦郟郏郵邮鄆郓鄉乡鄒邹鄔邬鄖郧鄟𫑘鄧邓鄩𬩽鄭郑鄰邻鄲郸鄳𫑡鄴邺鄶郐鄺邝酇酂酈郦醃腌醖酝醜丑醞酝醟蒏醣糖醫医醬酱醱酦醲𬪩醶𫑷釀酿釁衅釃酾釅酽釋释"
    "釐厘釒钅釓钆釔钇釕钌釗钊釘钉釙钋釚𫟲針针釟𫓥釣钓釤钐釦扣釧钏釨𫓦釩钒釲𫟳釳𨰿釴𬬩釵钗釷钍釹钕釺钎釾䥺釿𬬱鈀钯鈁钫鈃钘鈄钭鈅钥鈆𫓪鈇𫓧鈈钚鈉钠鈋𨱂鈍钝鈎钩鈐钤鈑钣"
    "鈒钑鈔钞鈕钮鈖𫟴鈗𫟵鈛𫓨鈞钧鈠𨱁鈡钟鈣钙鈥钬鈦钛鈧钪鈮铌鈯𨱄鈰铈鈲𨱃鈳钶鈴铃鈷钴鈸钹鈹铍鈺钰鈽钸鈾铀鈿钿鉀钾鉁𨱅鉅巨鉆钻鉈铊鉉铉鉊𬬿鉋铇鉍铋鉑铂鉔𫓬鉕钷鉗钳鉚铆"
    "鉛铅鉝𫟷鉞钺鉠𫓭鉢钵鉤钩鉥𬬸鉦钲鉧𬭁鉬钼鉭钽鉮𬬹鉳锫鉶铏鉷𫟹鉸铰鉺铒鉻铬鉽𫟸鉾𫓴鉿铪銀银銁𫓲銂𫟻銃铳銅铜銈𫓯銊𫓰銍铚銏𫟶銑铣銓铨銖铢銘铭銚铫銛铦銜衔銠铑銣铷銥铱"
    "銦铟銨铵銩铥銪铕銫铯銬铐銱铞銳锐銶𨱇銷销銹锈銻锑銼锉鋁铝鋂𰾄鋃锒鋅锌鋇钡鋉𨱈鋌铤鋏铗鋐𬭎鋒锋鋗𫓶鋙铻鋝锊鋟锓鋠𫓵鋣铘鋤锄鋥锃鋦锔鋨锇鋩铓鋪铺鋭锐鋮铖鋯锆鋰锂鋱铽"
    "鋶锍鋸锯鋹𬬮鋼钢錀𬬭錁锞錂𨱋錄录錆锖錇锫錈锩錏铔錐锥錒锕錕锟錘锤錙锱錚铮錛锛錜𫓻錝𫓽錞𬭚錟锬錠锭錡锜錢钱錤𫓹錥𫓾錦锦錨锚錩锠錫锡錮锢錯错録录錳锰錶表錸铼錼镎錽𫓸"
    "鍀锝鍁锨鍃锪鍄𨱉鍅钫鍆钔鍇锴鍈锳鍉𫔂鍊炼鍋锅鍍镀鍒𫔄鍔锷鍘铡鍚钖鍛锻鍠锽鍤锸鍥锲鍩锘鍬锹鍭𬭤鍮𨱎鍰锾鍵键鍶锶鍺锗鍼针鍾钟鎂镁鎄锿鎇镅鎈𫟿鎊镑鎌镰鎍𫔅鎓𬭩鎔镕鎖锁"
    "鎘镉鎙𫔈鎚锤鎛镈鎝𨱏鎞𫔇鎡镃鎢钨鎣蓥鎦镏鎧铠鎩铩鎪锼鎬镐鎭镇鎮镇鎯𨱍鎰镒鎲镋鎳镍鎵镓鎶鿔鎷𨰾鎸镌鎿镎鏃镞鏆𨱌鏇旋鏈链鏉𨱒鏌镆鏍镙鏏𬭬鏐镠鏑镝鏗铿鏘锵鏚𬭭鏜镗鏝镘"
    "鏞镛鏟铲鏡镜鏢镖鏤镂鏥𫔊鏦𫓩鏨錾鏰镚鏵铧鏷镤鏹镪鏺䥽鏻𬭸鏽锈鏾𫔌鐃铙鐄𨱑鐇𫔍鐈𫓱鐋铴鐍𫔎鐎𨱓鐏𨱔鐐镣鐒铹鐓镦鐔镡鐘钟鐙镫鐝镢鐠镨鐥䦅鐦锎鐧锏鐨镄鐩𬭼鐪𫓺鐫镌鐮镰"
    "鐯䦃鐲镯鐳镭鐵铁鐶镮鐸铎鐺铛鐼𫔁鐽𫟼鐿镱鑀𰾭鑄铸鑉𫠁鑊镬鑌镔鑑鉴鑒鉴鑔镲鑕锧鑞镴鑠铄鑣镳鑥镥鑪𬬻鑭镧鑰钥鑱镵鑲镶鑴𫔔鑷镊鑹镩鑼锣鑽钻鑾銮鑿凿钁镢钂镋長长門门閂闩"
    "閃闪閆闫閈闬閉闭開开閌闶閍𨸂閎闳閏闰閐𨸃閑闲閒闲間间閔闵閗𫔯閘闸閝𫠂閞𫔰閡阂閣阁閤合閥阀閨闺閩闽閫阃閬阆閭闾閱阅閲阅閵𫔴閶阊閹阉閻阎閼阏閽阍閾阈閿阌闃阒闆板闇暗"
    "闈闱闉𬮱闊阔闋阕闌阑闍阇闐阗闑𫔶闒阘闓闿闔阖闕阙闖闯關关闞阚闠阓闡阐闢辟闤阛闥闼陘陉陝陕陞升陣阵陰阴陳陈陸陆陽阳隉陧隊队階阶隑𬮿隕陨際际隤𬯎隨随險险隮𬯀隯陦隱隐"
    "隴陇隸隶隻只雋隽雖虽雙双雛雏雜杂雞鸡離离難难雲云電电霑沾霢霡霣𫕥霧雾霼𪵣霽霁靂雳靄霭靆叇靈灵靉叆靚靓靜静靝靔靦腼靧𫖃靨靥鞏巩鞝绱鞦秋鞽鞒鞾𫖇韁缰韃鞑韆千韉鞯韋韦"
    "韌韧韍韨韓韩韙韪韚𫠅韛𫖔韜韬韝鞲韞韫韠𫖒韻韵響响頁页頂顶頃顷項项順顺頇顸須须頊顼頌颂頍𫠆頎颀頏颃預预頑顽頒颁頓顿頔𬱖頗颇領领頜颌頠𬱟頡颉頤颐頦颏頫𫖯頭头頮颒頰颊"
    "頲颋頴颕頵𫖳頷颔頸颈頹颓頻频頽颓顂𩓋顃𩖖顅𫖶顆颗題题額额顎颚顏颜顒颙顓颛顔颜顗𫖮願愿顙颡顛颠類类顢颟顣𫖹顥颢顧顾顫颤顬颥顯显顰颦顱颅顳颞顴颧風风颭飐颮飑颯飒颰𩙥"
    "颱台颳刮颶飓颷𩙪颸飔颺飏颻飖颼飕颾𩙫飀飗飄飘飆飙飈飚飋𫗋飛飞飠饣飢饥飣饤飥饦飦𫗞飩饨飪饪飫饫飭饬飯饭飱飧飲饮飴饴飵𫗢飶𫗣飼饲飽饱飾饰飿饳餃饺餄饸餅饼餈糍餉饷養养"
    "餌饵餎饹餏饻餑饽餒馁餓饿餔𫗦餕馂餖饾餗𫗧餘余餚肴餛馄餜馃餞饯餡馅餦𫗠餧𫗪館馆餪𫗬餫𫗥餬糊餭𫗮餱糇餳饧餵喂餶馉餷馇餸𩠌餺馎餼饩餾馏餿馊饁馌饃馍饅馒饈馐饉馑饊馓饋馈"
    "饌馔饑饥饒饶饗飨饘𫗴饜餍饞馋饟𫗵饠𫗩饢馕馬马馭驭馮冯馯𫘛馱驮馳驰馴驯馹驲馼𫘜駁驳駃𫘝駉𬳶駊𫘟駎𩧨駐驻駑驽駒驹駓𬳵駔驵駕驾駘骀駙驸駚𩧫駛驶駝驼駞𫘞駟驷駡骂駢骈駤𫘠"
    "駧𩧲駩𩧴駪𬳽駫𫘡駭骇駰骃駱骆駶𩧺駸骎駻𫘣駼𬳿駿骏騁骋騂骍騃𫘤騄𫘧騅骓騉𫘥騊𫘦騌骔騍骒騎骑騏骐騑𬴂騔𩨀騖骛騙骗騚𩨊騜𫘩騝𩨃騞𬴃騟𩨈騠𫘨騤骙騧䯄騪𩨄騫骞騭骘騮骝騰腾"
    "騱𫘬騴𫘫騵𫘪騶驺騷骚騸骟騻𫘭騼𫠋騾骡驀蓦驁骜驂骖驃骠驄骢驅驱驊骅驋𩧯驌骕驍骁驎𬴊驏骣驓𫘯驕骄驗验驙𫘰驚惊驛驿驟骤驢驴驤骧驥骥驦骦驨𫘱驪骊驫骉骯肮髏髅髒脏體体髕髌"
    "髖髋髮发鬆松鬍胡鬖𩭹鬚须鬠𫘽鬢鬓鬥斗鬧闹鬨哄鬩阋鬮阄鬱郁鬹鬶魎魉魘魇魚鱼魛鱽魟𫚉魢鱾魥𩽹魦𫚌魨鲀魯鲁魴鲂魵𫚍魷鱿魺鲄魽𫠐鮀𬶍鮁鲅鮃鲆鮄𫚒鮅𫚑鮆𫚖鮈𬶋鮊鲌鮋鲉鮍鲏"
    "鮎鲇鮐鲐鮑鲍鮒鲋鮓鲊鮚鲒鮜鲘鮝鲞鮞鲕鮟𩽾鮠𬶏鮡𬶐鮣䲟鮤𫚓鮦鲖鮪鲔鮫鲛鮭鲑鮮鲜鮯𫚗鮰𫚔鮳鲓鮵𫚛鮶鲪鮸𩾃鮺鲝鮿𫚚鯀鲧鯁鲠鯄𩾁鯆𫚙鯇鲩鯉鲤鯊鲨鯒鲬鯔鲻鯕鲯鯖鲭鯗鲞鯛鲷"
    "鯝鲴鯞𫚡鯡鲱鯢鲵鯤鲲鯧鲳鯨鲸鯪鲮鯫鲰鯬𫚞鯰鲶鯱𩾇鯴鲺鯶𩽼鯷鳀鯻𬶟鯽鲫鯾𫚣鯿鳊鰁鳈鰂鲗鰃鳂鰆䲠鰈鲽鰉鳇鰊𬶠鰋𫚢鰌䲡鰍鳅鰏鲾鰐鳄鰑𫚊鰒鳆鰓鳃鰕𫚥鰛鳁鰜鳒鰟鳑鰠鳋鰣鲥"
    "鰤𫚕鰥鳏鰦𫚤鰧䲢鰨鳎鰩鳐鰫𫚦鰭鳍鰮鳁鰱鲢鰲鳌鰳鳓鰵鳘鰶𬶭鰷鲦鰹鲣鰺鲹鰻鳗鰼鳛鰽𫚧鰾鳔鱀𬶨鱂鳉鱄𫚋鱅鳙鱆𫠒鱇𩾌鱈鳕鱉鳖鱊𫚪鱒鳟鱔鳝鱖鳜鱗鳞鱘鲟鱚𬶮鱝鲼鱟鲎鱠鲙鱢𫚫"
    "鱣鳣鱤鳡鱧鳢鱨鲿鱭鲚鱮𫚈鱯鳠鱲𫚭鱷鳄鱸鲈鱺鲡鳥鸟鳧凫鳩鸠鳬凫鳲鸤鳳凤鳴鸣鳶鸢鳷𫛛鳼𪉃鳽𫛚鳾䴓鴀𫛜鴃𫛞鴅𫛝鴆鸩鴇鸨鴉鸦鴐𫛤鴒鸰鴔𫛡鴕鸵鴗𫁡鴛鸳鴜𪉈鴝鸲鴞鸮鴟鸱鴣鸪"
    "鴥𫛣鴦鸯鴨鸭鴮𫛦鴯鸸鴰鸹鴲𪉆鴳𫛩鴴鸻鴷䴕鴻鸿鴽𫛪鴿鸽鵁䴔鵂鸺鵃鸼鵊𫛥鵏𬷕鵐鹀鵑鹃鵒鹆鵓鹁鵚𪉍鵜鹈鵝鹅鵟𫛭鵠鹄鵡鹉鵧𫛨鵩𫛳鵪鹌鵫𫛱鵬鹏鵮鹐鵯鹎鵰雕鵲鹊鵷鹓鵾鹍鶄䴖"
    "鶇鸫鶉鹑鶊鹒鶌𫛵鶒𫛶鶓鹋鶖鹙鶗𫛸鶘鹕鶚鹗鶠𬸘鶡鹖鶥鹛鶦𫛷鶩鹜鶪䴗鶬鸧鶭𫛯鶯莺鶰𫛫鶱𬸣鶲鹟鶴鹤鶹鹠鶺鹡鶻鹘鶼鹣鶿鹚鷀鹚鷁鹢鷂鹞鷄鸡鷅𫛽鷉䴘鷊鹝鷐𫜀鷓鹧鷔𪉑鷖鹥鷗鸥"
    "鷙鸷鷚鹨鷟𬸦鷣𫜃鷤𫛴鷥鸶鷦鹪鷨𪉊鷩𫜁鷫鹔鷭𬸪鷯鹩鷲鹫鷳鹇鷴鹇鷷𫜄鷸鹬鷹鹰鷺鹭鷽鸴鷿𬸯鸂㶉鸇鹯鸊䴙鸋𫛢鸌鹱鸏鹲鸑𬸚鸕鸬鸗𫛟鸘鹴鸚鹦鸛鹳鸝鹂鸞鸾鹵卤鹹咸鹺鹾鹼碱鹽盐"
    "麗丽麥麦麨𪎊麩麸麪面麫面麬𤿲麯曲麲𪎉麳𪎌麴曲麵面麷𫜑麼么麽么黃黄黌黉點点黨党黲黪黴霉黶黡黷黩黽黾黿鼋鼂鼌鼉鼍鼕冬鼴鼹齊齐齋斋齎赍齏齑齒齿齔龀齕龁齗龂齘𬹼齙龅齜龇"
    "齟龃齠龆齡龄齣出齦龈齧啮齩𫜪齪龊齬龉齭𫜭齮𬺈齯𫠜齰𫜬齲龋齴𫜮齶腭齷龌齼𬺓齾𫜰龍龙龎厐龐庞龑䶮龓𫜲龔龚龕龛龜龟龭𩨎龯𨱆鿁䜤鿓鿒𠁞𠀾𠌥𠆿𠏢𠉗𠐊𫝋𠗣㓆𠞆𠛆𠠎𠚳𠬙𪠡𠽃𪠺"
    "𠿕𪜎𡂡𪢒𡃄𪡺𡃕𠴛𡃤𪢐𡄔𠴢𡄣𠵸𡅏𠲥𡅯𪢖𡑍𫭼𡑭𡋗𡓁𪤄𡓾𡋀𡔖𡍣𡞵㛟𡟫𫝪𡠹㛿𡢃㛠𡮉𡭜𡮣𡭬𡳳𡳃𡸗𪨩𡹬𪨹𡻕岁𡽗𡸃𡾱㟜𡿖𪩛𢍰𪪴𢠼𢙑𢣐𪬚𢣚𢘝𢣭𢘞𢤩𪫡𢤱𢘙𢤿𪬯𢯷𪭝𢶒𪭯𢶫𢫞𢷮𢫊𢹿𢬦"
    "𢺳𪮳𣈶暅𣋋𣈣𣍐𫧃𣙎㭣𣜬𪳗𣝕𣘷𣞻𣘓𣠩𣞎𣠲𣑶𣯩𣯣𣯴𣭤𣯶毶𣽏𪶮𣾷㳢𣿉𣶫𤁣𣺽𤄷𪶒𤅶𣷷𤑳𤎻𤑹𪹀𤒎𤊀𤒻𪹹𤓌𪹠𤓎𤎺𤓩𤊰𤘀𪺣𤛮𤙯𤛱𫞢𤜆𪺪𤠮𪺸𤢟𤝢𤢻𢢐𤩂𫞧𤪺㻘𤫩㻏𤬅𪼴𤳷𪽝𤳸𤳄𤷃𪽭"
    "𤸫𤶧𤺔𪽴𥊝𥅿𥌃𥅘𥏝𪿊𥕥𥐰𥖅𥐯𥖲𪿞𥗇𪿵𥗽𬒗𥜐𫀓𥜰𫀌𥞵𥞦𥢢䅪𥢶𫞷𥢷𫀮𥨐𥧂𥪂𥩺𥯤𫁳𥴨𫂖𥴼𫁺𥵃𥱔𥵊𥭉𥶽𫁱𥸠𥮋𥻦𫂿𥼽𥹥𥽖𥺇𥾯𫄝𥿊𦈈𦀖𫄦𦂅𦈒𦃄𦈗𦃩𫄯𦅇𫄪𦅈𫄵𦆲𫟇𦒀𫅥𦔖𫅼𦘧𡳒"
    "𦟼𫆝𦠅𫞅𦡝𫆫𦢈𣍨𦣎𦟗𦧺𫇘𦪙䑽𦪽𦨩𦱌𫇪𦾟𦶻𧎈𧌥𧒯𫊹𧔥𧒭𧕟𧉐𧜗䘞𧜵䙊𧝞䘛𧞫𫌋𧟀𧝧𧡴𫌫𧢄𫌬𧦝𫍞𧦧𫍟𧩕𫍭𧩙䜥𧩼𫍶𧫝𫍺𧬤𫍼𧭈𫍾𧭹𫍐𧳟𧳕𧵳䞌𧶔𧹓𧶧䞎𧷎𪠀𧸘𫎨𧹈𪥠𧽯𫎸𨂐𫏌𨄣𨀱"
    "𨅍𨁴𨆪𫏕𨇁𧿈𨇞𨅫𨇤𫏨𨇰𫏞𨇽𫏑𨈊𨂺𨈌𨄄𨊰䢀𨊸䢁𨊻𨐆𨋢䢂𨌈𫐍𨍰𫐔𨎌𫐋𨎮𨐉𨏠𨐇𨏥𨐊𨞺𫟫𨟊𫟬𨢿𨡙𨣈𨡺𨣞𨟳𨣧𨠨𨤻𨤰𨥛𨱀𨥟𫓫𨦫䦀𨧀𬭊𨧜䦁𨧰𫟽𨧱𨱊𨨏𬭛𨨛𫓼𨨢𫓿𨩰𫟾𨪕𫓮𨫒𨱐𨬖𫔏"
    "𨭆𬭶𨭎𬭳𨭖𫔑𨭸𫔐𨮂𨱕𨮳𫔒𨯅䥿𨯟𫔓𨰃𫔉𨰋𫓳𨰥𫔕𨰲𫔃𨲳𫔖𨳑𨸁𨳕𨸀𨴗𨸅𨴹𫔲𨵩𨸆𨵸𨸇𨶀𨸉𨶏𨸊𨶮𨸌𨶲𨸋𨷲𨸎𨼳𫔽𨽏𨸘𩀨𫕚𩅙𫕨𩎖𫖑𩎢𩏾𩏂𫖓𩏠𫖖𩏪𩏽𩏷𫃗𩑔𫖪𩒎𫖭𩓣𩖕𩓥𫖵𩔑𫖷𩔳𫖴"
    "𩖰𫠇𩗀𩙦𩗓𫗈𩗴𫗉𩘀𩙩𩘝𩙭𩘹𩙨𩘺𩙬𩙈𩙰𩚛𩟿𩚥𩠀𩚩𫗡𩚵𩠁𩛆𩠂𩛌𫗤𩛡𫗨𩛩𩠃𩜇𩠉𩜦𩠆𩜵𩠊𩝔𩠋𩝽𫗳𩞄𩠎𩞦𩠏𩞯䭪𩟐𩠅𩟗𫗚𩠴𩠠𩡣𩡖𩡺𩧦𩢡𩧬𩢴𩧵𩢸𩧳𩢾𩧮𩣏𩧶𩣑䯃𩣫𩧸𩣵𩧻𩣺𩧼𩤊𩧩"
    "𩤙𩨆𩤲𩨉𩤸𩨅𩥄𩨋𩥇𩨍𩥉𩧱𩥑𩨌𩦠𫠌𩧆𩨐𩭙𩬣𩯁𫙂𩯳𩯒𩰀𩬤𩰹𩰰𩳤𩲒𩴵𩴌𩵦𫠏𩵩𩽺𩵹𩽻𩶁𫚎𩶘䲞𩶰𩽿𩶱𩽽𩷰𩾄𩸃𩾅𩸄𫚝𩸡𫚟𩸦𩾆𩻗𫚨𩻬𫚩𩻮𫚘𩼶𫚬𩽇𩾎𩿅𫠖𩿤𫛠𩿪𪉄𪀖𫛧𪀦𪉅𪀾𪉋𪁈𪉉"
    "𪁖𪉌𪂆𪉎𪃍𪉐𪃏𪉏𪃒𫛻𪃧𫛹𪄆𪉔𪄕𪉒𪅂𫜂𪆷𫛾𪇳𪉕𪈼𱊜𪉸𫜊𪋿𫧮𪌭𫜓𪍠𫜕𪓰𫜟𪔵𪔭𪘀𪚏𪘯𪚐𪙏𫜯𪟖𠛾𪷓𣶭𫒡𫓷𫜦𫜫"
)
# 침구 문헌 이체자 접기(검색용): 䯒·骭→胻(정강이), 臁→廉, 窌→髎, 鬲→膈, 腧·输→俞(수혈)
_VARIANT_PAIRS = "䯒胻骭胻臁廉窌髎鬲膈腧俞输俞"
_T2S_TABLE = {ord(_T2S_PAIRS[i]): _T2S_PAIRS[i + 1] for i in range(0, len(_T2S_PAIRS), 2)}
_T2S_TABLE.update({ord(_VARIANT_PAIRS[i]): _VARIANT_PAIRS[i + 1] for i in range(0, len(_VARIANT_PAIRS), 2)})
_OPENCC = []
_COMPACT_RE = re.compile(
    r"[\s\u3000-\u303f\uff00-\uff0f\uff1a-\uff20\uff3b-\uff40\uff5b-\uff65"
    r"“”‘’\"'《》〈〉「」『』【】（）()\[\]{}<>…·—–\-*_#|`~:;,.!?、，。；：！？]"
)


def norm_text(text):
    """번체·이체자를 간체로 맞춘다(표 기반이라 빠르다)."""
    return (text or "").translate(_T2S_TABLE)


def norm_query(text):
    if not _OPENCC:
        try:
            import opencc
            _OPENCC.append(opencc.OpenCC("t2s").convert)
        except Exception:
            _OPENCC.append(None)
    if _OPENCC[0]:
        try:
            text = _OPENCC[0](text)
        except Exception:
            pass
    return norm_text(text)


def compact(text):
    """공백·문장부호·마크다운 기호를 지운 비교용 문자열."""
    return _COMPACT_RE.sub("", text or "")


# ---------------------------------------------------------------------------
# 기본 데이터
# ---------------------------------------------------------------------------
def ncode(code):
    """'ST036'·'st 36'·'LU06' → 'ST36'·'LU6' (영문 2자+숫자 코드만 정규화)"""
    m = re.match(r"^([A-Za-z]{2})\s*-?\s*0*(\d+)$", str(code or "").strip())
    return f"{m.group(1).upper()}{int(m.group(2))}" if m else str(code or "").strip().upper()


def _load_json(key):
    text = BACKEND.read_text(key)
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception as e:
        sys.stderr.write(f"[acupoint-core] {key} JSON parse error: {e}\n")
        return {}


def points():
    """마스터 CSV → {조회 키: 경혈 레코드}. 키: 코드(원형·0 제거·0 채움), 한글명, 한자명(원형·간체)"""
    def load():
        out = {}
        text = BACKEND.read_text("master_csv")
        if not text:
            return out
        for row in csv.DictReader(io.StringIO(text.lstrip("\ufeff"))):
            code = (row.get("경혈코드") or "").strip()
            if not code:
                continue
            rec = {
                "code": code,
                "ncode": ncode(code),
                "name_kr": (row.get("본혈명(한글)") or "").strip(),
                "name_cn": (row.get("본혈명(한자)") or "").strip(),
                "meridian_cn": (row.get("소속경락(한자)") or "").strip(),
                "meridian_kr": (row.get("소속경락(한글)") or "").strip(),
                "aliases_hanja": (row.get("이명_한자목록(KJH)") or "").strip(),
                "aliases_hangul": (row.get("이명_한글독음목록(KJH)") or "").strip(),
                "volume": (row.get("혈위통감_권차") or "").strip(),
                "classics": (row.get("출전_및_근거문헌") or "").strip(),
            }
            m = re.match(r"([A-Z]+)0*(\d+)", code.upper())
            keys = {code.upper(), rec["ncode"]}
            if m:
                keys.add(f"{m.group(1)}{int(m.group(2)):02d}")
            keys.update(k for k in (rec["name_kr"], rec["name_cn"], norm_text(rec["name_cn"])) if k)
            for k in keys:
                out.setdefault(k, rec)
        return out
    return _cached("points", load)


def resolve_point(query):
    q = (query or "").strip()
    if not q:
        return None
    pts = points()
    for k in (q, q.upper(), ncode(q), norm_query(q)):
        if k in pts:
            return pts[k]
    return None


def all_point_names():
    """간체 혈명 집합(별명 충돌 판정용)"""
    return _cached("point_names", lambda: {norm_text(p["name_cn"]) for p in points().values() if p.get("name_cn")})


def biomed():
    return _cached("biomed", lambda: _load_json("biomed_json"))


def reference():
    return _cached("reference", lambda: _load_json("reference_json"))


def framework_text():
    return _cached("framework", lambda: BACKEND.read_text("framework") or "")


def framework_version():
    m = re.search(r"공식 버전\*\*:\s*([^—\n]+)", framework_text())
    return m.group(1).strip() if m else "확인 불가"


MERIDIAN_KEYS = {  # 코드 접두어 → 간체 경맥명(원전 파일명·동의보감 경맥 제목과 대조)
    "LU": "手太阴肺经", "LI": "手阳明大肠经", "ST": "足阳明胃经", "SP": "足太阴脾经",
    "HT": "手少阴心经", "SI": "手太阳小肠经", "BL": "足太阳膀胱经", "KI": "足少阴肾经",
    "PC": "手厥阴心包经", "TE": "手少阳三焦经", "SJ": "手少阳三焦经", "GB": "足少阳胆经",
    "LR": "足厥阴肝经", "LV": "足厥阴肝经", "GV": "督脉", "DU": "督脉", "CV": "任脉",
    "RN": "任脉", "EX": "经外",
}


# ---------------------------------------------------------------------------
# 도구 1: 경혈 프로파일 (데이터 기반)
# ---------------------------------------------------------------------------
FEN_MM = 2.3


def _fen_text(v):
    if v is None or v == "":
        return "미기술"
    if isinstance(v, (int, float)):
        return "**금침(0)**" if v == 0 else f"{v:g}푼 = {v * FEN_MM:.1f}mm"
    return str(v)


def handle_get_acupoint_anatomy_profile(args):
    target = (args.get("acupoint") or args.get("code") or args.get("name") or "").strip()
    p = resolve_point(target)
    if not p:
        return f"⚠ 경혈 '{target}'을(를) 마스터 DB에서 찾지 못했습니다. 코드(ST36, LU5) 또는 한글·한자 혈명을 확인하세요."
    code = p["ncode"]
    ref = reference().get("acupoints", {}).get(code, {})
    bdb = biomed()
    entry = bdb.get(code) if isinstance(bdb.get(code), dict) else {}

    out = [
        f"# 📍 [{p['code']}] {p['name_kr']} ({p['name_cn']}) — 데이터 프로파일",
        f"- **소속 경락**: {p['meridian_kr']} ({p['meridian_cn']})",
        f"- **KJH 이명**: {p['aliases_hanja'] or '-'} [{p['aliases_hangul'] or '-'}]",
        f"- **마스터 CSV 출전 표기**: {p['classics'] or '-'} · 《穴位通鉴》 권차: {p['volume'] or '-'}",
        "",
        "## 1. 2대 교재 해부구조 (교재 데이터셋)",
    ]
    tb = ref.get("textbooks", {})
    if tb:
        out += ["| 구분 | 경혈학 공통교재 | 김재효 교재 | 비교 |", "| :--- | :--- | :--- | :--- |"]
        for cat in ("근육", "신경", "혈관"):
            a = tb.get("공통교재", {}).get(cat, [])
            b = tb.get("김재효", {}).get(cat, [])
            ka, kb = {x["ko"] for x in a}, {x["ko"] for x in b}
            cmp_txt = "일치" if ka == kb else ("공통교재 단독: " + ", ".join(sorted(ka - kb)) if ka - kb else "") + \
                (" / " if (ka - kb) and (kb - ka) else "") + ("김재효 단독: " + ", ".join(sorted(kb - ka)) if kb - ka else "")
            fmt = lambda xs: "<br>".join(f"{x['ko']} ({x['en']})" if x.get("en") else x["ko"] for x in xs) or "—"
            out.append(f"| {cat} | {fmt(a)} | {fmt(b)} | {cmp_txt or '—'} |")
        out.append("- 층차(Layer 1~5) 배치는 교재에 없으므로 이 도구는 나누지 않는다. FMA 실체·지배신경·분절은 `get_fma_anatomy_profile`로 확인한다.")
    else:
        out.append("- 교재 데이터셋에 이 경혈 행이 없습니다.")

    out += ["", "## 2. 문헌별 자침 깊이 (한대 1푼 = 2.3mm)"]
    dp = ref.get("depth_fen", {})
    if dp:
        out += ["| 문헌·교재 | 기재값 | 환산 |", "| :--- | :---: | :--- |"]
        for src, v in dp.items():
            if isinstance(v, str) or "선호되는 자침법" in src:
                if v:
                    out.append(f"| {src} | {v} | — |")
                continue
            out.append(f"| {src} | {'' if v is None else v} | {_fen_text(v)} |")
        out.append("- 0=금침, 빈칸=미기술(자침깊이 데이터셋 규칙). 도달 Layer와 안전 범위는 해부 실측과 대조해 판단한다(Rank 5).")
    else:
        out.append("- 자침깊이 데이터셋에 이 경혈 행이 없습니다.")

    out += ["", "## 3. 통합 생의학 마스터 DB (Layer A) 요약"]
    if entry:
        active = {x.get("id") for x in bdb.get("papers", []) if x.get("status", "active") == "active"}
        inv = set(bdb.get("acupoint_inverted_index", {}).get(code, []))
        out += [
            f"- **역색인 논문**: {len(inv)}편 (그중 active {len(inv & active)}편) · 로컬 매핑 {entry.get('local_papers_count', 0)}편 · 외부 {entry.get('external_papers_count', 0)}편 · 랜드마크 {len(entry.get('landmark_paper_ids', []))}편 · 마지막 API 동기화 {entry.get('last_api_sync_at', '-')}",
            f"- **DB 기재 신경·혈관**: {entry.get('innervation_anatomy', '-')}",
            f"- **DB 기재 척수 분절**: {entry.get('spinal_segment', '-')}",
            f"- **DB 기재 반사 회로**: {entry.get('reflex_circuit', '-')}",
            "- 위 세 줄은 DB에 적힌 요약값이다. 기전 판정은 논문 원문과 Layer B B-Check(≥ 8/12, ①·② ≥ 1)로 한다. 논문 목록은 `search_biomedical_reflex_db`.",
        ]
    else:
        out.append("- 통합 DB에 이 경혈 항목이 없습니다.")

    out += ["", "## 4. 기존 Tier 3 보고서"]
    reps = ref.get("reports", [])
    if reps:
        for r in reps:
            out.append(f"- `{r['path']}` — {r['title']}")
            for line in r.get("ari_lines", []):
                out.append(f"  - {line}")
    else:
        out.append("- 없음. Tri-Target 공간 변위 분기·ARI v3.0은 원전 대조(Rank 1~5)와 이중 채점(Rank 7)으로 산출해야 하며 이 도구는 값을 만들지 않는다.")

    out += ["", f"> 출처: 마스터 CSV · 교재·자침깊이 데이터셋(참조 JSON) · 통합 생의학 마스터 DB · 보고서 색인 ({BACKEND.label}). 정본 {framework_version()}."]
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 도구 2: FMA 프로파일
# ---------------------------------------------------------------------------
def handle_get_fma_anatomy_profile(args):
    target = (args.get("acupoint") or args.get("code") or args.get("name") or "").strip()
    p = resolve_point(target)
    code = p["code"] if p else target.upper()
    name_kr = p["name_kr"] if p else ""
    out_format = (args.get("format") or "markdown").strip().lower()
    m = re.match(r"([A-Za-z]+)\s*0*(\d+)", code)
    fma_code = f"{m.group(1).upper()}{int(m.group(2)):02d}" if m else code

    inst, fq = BACKEND.fma_instance()
    if inst is not None and fq is not None:
        try:
            prof = fq.build_profile(inst, fma_code)
            return _fma_markdown_from_index(prof) if out_format != "json" else json.dumps(
                prof, ensure_ascii=False, indent=2, default=lambda o: sorted(o) if isinstance(o, set) else str(o))
        except BaseException as e:  # fma_query는 실패 시 sys.exit()를 부른다 — 서버가 죽지 않도록 잡고 JSON 대응표로 대체
            sys.stderr.write(f"[acupoint-core] FMA 색인 조회 실패({e}); 대응표 JSON으로 대체\n")

    rows = [r for r in _cached("fma", lambda: _load_json("fma_json")).get("rows", []) if ncode(r.get("code", "")) == ncode(fma_code)]
    if not rows:
        return f"⚠ 경혈 '{target}' ({fma_code})의 FMA 대응 행을 찾지 못했습니다."
    if out_format == "json":
        return json.dumps({"code": fma_code, "name_kr": name_kr or rows[0].get("name_kr", ""), "rows": rows}, ensure_ascii=False, indent=2)
    order = {"근육": 0, "신경": 1, "혈관": 2}
    rows = sorted(rows, key=lambda r: (order.get(r.get("category"), 9), r.get("fma_label") or "~"))
    out = [
        f"# 🏛️ [FMA 5.1.0] {fma_code} {name_kr or rows[0].get('name_kr', '')} — 교재 용어 ↔ FMA 대응표",
        f"- **원천**: 경혈↔FMA 대응표(2대 교재 통합, {len(rows)}행). 지배신경 줄기·분절은 로컬 FMA 색인이 있을 때만 나온다.",
        "",
        "| 구분 | 교재 한글명 | 교재 영문명 | FMA 실체 | 대응 수준 | 출처 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    ids_by_src = {}
    for r in rows:
        fid = r.get("fma_id")
        if fid:
            ids_by_src.setdefault(r.get("source") or "미상", set()).add(fid)
        out.append(f"| {r.get('category') or '기타'} | {r.get('term_kr') or '-'} | {r.get('term_en') or '-'} | "
                   f"{('FMA:' + str(fid) + ' ' + (r.get('fma_label') or '')) if fid else '—'} | {r.get('match') or 'none'} | {r.get('source') or '미상'} |")
    common = set.intersection(*ids_by_src.values()) if len(ids_by_src) >= 2 else set()
    out += ["", "## 2대 교재 비교", *[f"- **{s}**: FMA 실체 {len(v)}개" for s, v in ids_by_src.items()],
            f"- **공통 FMA 실체**: {len(common)}개", "",
            "> 대응 수준: `exact`=완전 일치(확정 근거), `parent`=상위 구조 대응(가지 미등재), `none`=FMA 미등재"]
    return "\n".join(out)


def _fma_markdown_from_index(p):
    order = {"근육": 0, "신경": 1, "혈관": 2}
    structs = sorted(p["structures"], key=lambda s: (order.get(s["category"], 9), s["fma_label"] or "~"))
    out = [
        f"# 🏛️ [FMA 5.1.0] {p['code']} {p['name_kr']} — 해부 실체 온톨로지 프로파일",
        f"- **원천**: FMA 5.1.0 로컬 색인 · 대응 실체 {len(structs)}개",
        "",
        "| 구분 | 교재 용어 | FMA 실체 | 대응 수준 | 출처 | 신경 지배 / 상위 줄기 | 척수 분절 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for s in structs:
        terms = "<br>".join(sorted(s["terms"]))
        srcs = "·".join(sorted(s["sources"]))
        if not s["fma_id"]:
            out.append(f"| {s['category']} | {terms} | — | none | {srcs} | — | — |")
            continue
        rel = s.get("relations", {})
        if rel.get("nerve_supply"):
            nerve = "<br>".join(
                f"FMA:{nid} {lab}" + ((" → " + " → ".join(l2 for _, l2 in s["nerve_trunks"].get(nid, [])[:3])) if s["nerve_trunks"].get(nid) else "")
                for nid, lab in rel["nerve_supply"][:3])
        else:
            nerve = " → ".join(f"FMA:{o} {lab}" for o, lab in s.get("branch_chain", [])[:4]) or "—"
        seg = s.get("segments", {})
        segtxt = ", ".join(f"{k}({'/'.join(v)})" for k, v in seg.get("direct", {}).items()) or \
            ((", ".join(seg.get("inferred_from_nerve_chain", [])) + " (신경 경로 추론)") if seg.get("inferred_from_nerve_chain") else "—")
        out.append(f"| {s['category']} | {terms} | FMA:{s['fma_id']} {s['fma_label']} | {'/'.join(sorted(s['match']))} | {srcs} | {nerve} | {segtxt} |")
    seg_union = p.get("segment_union", {})
    out += ["", "## 척수 분절 합집합 (B-Check ② 입력)",
            f"- **{', '.join(seg_union)}**" if seg_union else "- FMA에 기재된 분절 없음",
            *[f"  - `{k}`: {', '.join(v)}" for k, v in seg_union.items()]]
    tc = p.get("textbook_compare", {})
    out += ["", "## 2대 교재 비교 (10대 구성 요소 ⑥)",
            f"- 공통 FMA 실체 {len(tc.get('common', []))}개 · 공통교재 단독 {len(tc.get('only_공통교재', []))}개 · 김재효 단독 {len(tc.get('only_김재효', []))}개",
            "", "> 대응 수준: `exact`=완전 일치(확정 근거), `parent`=상위 구조 대응(가지 미등재), `none`=FMA 미등재"]
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 도구 3: 생의학 DB 검색 (Layer A)
# ---------------------------------------------------------------------------
_HUMAN_RE = re.compile(r"\b(patients?|participants?|volunteers?|subjects|healthy (?:adults?|men|women)|humans?|randomi[sz]ed|clinical trial|rct|fmri|cohort|case report|women|men|children)\b|임상|환자|피험자", re.I)
_ANIMAL_RE = re.compile(r"\b(rats?|mice|mouse|murine|rabbits?|cats?|dogs?|monkeys?|rodents?|animals?|guinea pigs?|piglets?|zebrafish)\b|동물|쥐|흰쥐", re.I)
_REVIEW_RE = re.compile(r"\b(review|meta-analysis|systematic)\b|고찰|리뷰|종설", re.I)
_MECH_RE = re.compile(r"\b(mechanism|pathway|neurons?|nerves?|receptors?|vagal|vagus|spinal|reflex|afferent|efferent|c-fos|signaling)\b|기전|신경|반사|수용체", re.I)
_INACTIVE = {"duplicate", "missing", "superseded"}


def _design_guess(p):
    text = " ".join(str(p.get(k) or "") for k in ("title", "abstract_snippet", "journal"))
    tags = []
    if _REVIEW_RE.search(text):
        tags.append("리뷰")
    if _HUMAN_RE.search(text):
        tags.append("인체")
    if _ANIMAL_RE.search(text):
        tags.append("동물")
    return tags


def handle_search_biomedical_reflex_db(args):
    query = (args.get("query") or args.get("acupoint") or args.get("code") or "").strip()
    flt = (args.get("evidence_filter") or "all").lower()
    include_inactive = bool(args.get("include_inactive"))
    try:
        limit = max(1, min(int(args.get("limit") or 10), 50))
    except (TypeError, ValueError):
        limit = 10
    if not query:
        return "⚠ `query`(경혈 코드·혈명 또는 키워드)를 입력하세요."
    db = biomed()
    papers = db.get("papers", [])
    if isinstance(papers, dict):
        papers = [{"id": k, **v} for k, v in papers.items()]
    if not papers:
        return "⚠ 통합 생의학 마스터 DB를 읽지 못했습니다."

    pt = resolve_point(query)
    scored = {}
    head = []
    if pt:  # 경혈 모드: 역색인·검출 혈위·랜드마크를 정확한 코드로 대조
        code = pt["ncode"]
        entry = db.get(code) if isinstance(db.get(code), dict) else {}
        landmark = set(entry.get("landmark_paper_ids", []))
        inv = set(db.get("acupoint_inverted_index", {}).get(code, []))
        names = {pt["name_cn"], norm_text(pt["name_cn"]), pt["name_kr"]}
        for p in papers:
            s = 0
            pid = p.get("id")
            if pid in landmark:
                s += 10
            if pid in inv:
                s += 8
            if code in {ncode(c) for c in (p.get("detected_acupoints") or [])}:
                s += 5
            title = str(p.get("title") or "")
            if re.search(rf"\b{re.escape(code)}\b", title, re.I) or any(n and n in title for n in names):
                s += 3
            if s:
                scored[pid] = (s, p)
        head = [f"- **경혈 모드**: {pt['code']} {pt['name_kr']}({pt['name_cn']}) — 랜드마크 {len(landmark)}편 · 역색인 {len(inv)}편 · 검출 혈위/제목 대조"]
        if entry:
            head.append(f"- **DB 기재 반사 회로(요약값)**: {entry.get('reflex_circuit', '-')}")
    else:  # 키워드 모드: 모든 검색어가 제목·초록·키워드·MeSH·저널 어딘가에 있어야 함
        terms = [t.lower() for t in query.split()]
        for p in papers:
            fields = {k: str(p.get(k) or "").lower() for k in ("title", "abstract_snippet", "journal")}
            fields["kw"] = " ".join(map(str, p.get("keywords") or [])).lower() + " " + " ".join(map(str, p.get("mesh") or [])).lower()
            blob = " ".join(fields.values())
            if not all(t in blob for t in terms):
                continue
            s = sum(6 for t in terms if t in fields["title"]) + sum(3 for t in terms if t in fields["kw"]) + \
                sum(2 for t in terms if t in fields["abstract_snippet"]) + sum(1 for t in terms if t in fields["journal"])
            scored[p.get("id")] = (s, p)
        head = [f"- **키워드 모드**: {' + '.join(terms)}"]

    rows, hidden = [], 0
    for pid, (s, p) in sorted(scored.items(), key=lambda kv: (-kv[1][0], -(kv[1][1].get("year") or 0))):
        status = p.get("status") or "active"
        if status in _INACTIVE and not include_inactive:
            hidden += 1
            continue
        tags = _design_guess(p)
        if flt == "human" and "인체" not in tags:
            continue
        if flt == "animal" and "동물" not in tags:
            continue
        if flt == "review" and "리뷰" not in tags:
            continue
        if flt == "mechanism" and not _MECH_RE.search(" ".join(str(p.get(k) or "") for k in ("title", "abstract_snippet"))):
            continue
        rows.append((pid, p, tags, status))
    total = len(rows)
    out = [f"# 🔬 [Layer A] 통합 생의학 마스터 DB 검색: '{query}' — {total}편 중 {min(total, limit)}편 표시", *head,
           f"- **일치** {len(scored)}편 → 인용 제외 상태(duplicate·missing·superseded) {'포함' if include_inactive else f'{hidden}편 숨김'}"
           f" → 설계 필터 '{flt}' 적용 후 {total}편",
           "- 설계 구분(인체·동물·리뷰)은 DB에 기록이 없어 **제목·초록 키워드로 추정**한 값이다. 인용 전 원문으로 확인한다.", ""]
    for i, (pid, p, tags, status) in enumerate(rows[:limit], 1):
        ident = " · ".join(x for x in (f"PMID {p['pmid']}" if p.get("pmid") else "", f"DOI {p['doi']}" if p.get("doi") else "") if x) or "식별자 없음(로컬 파일)"
        out.append(f"### [{i}] papers.id {pid} — {p.get('title') or p.get('filename') or '제목 없음'}")
        out.append(f"- {p.get('year') or '-'} · *{p.get('journal') or '-'}* · {ident} · 상태 {status} · 설계(추정) {'/'.join(tags) or '미분류'}")
        det = p.get("detected_acupoints") or []
        if det:
            out.append(f"- 검출 혈위: {', '.join(det[:12])}{' …' if len(det) > 12 else ''}")
        snip = str(p.get("abstract_snippet") or "").strip()
        if snip and not snip.startswith(str(p.get("journal") or "@@")):
            out.append(f"- 초록 발췌: {snip[:220]}{'…' if len(snip) > 220 else ''}")
        out.append("")
    if not rows:
        out.append("적중 논문이 없습니다.")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 도구 4: Layer B 등록부
# ---------------------------------------------------------------------------
BCHECK_RULE = [
    "B-Check 6항목(① 말초 실체 ② 분절 정합 ③ 구심 섬유·수용체 ④ 중추 경로 ⑤ 원심 효과 방향 ⑥ 인체 전환)을 각 0/1/2점으로 채점한다.",
    "합계 ≥ {thr}이고 ①·② ≥ 1일 때만 기전을 확정 기술한다(정본 Rank 6-5).",
    "③~⑤가 동물 근거뿐이고 ⑥ = 0이면 '(동물 한정)', 상충 근거가 있으면 '가설'로 제한한다.",
    "종·마취·검증 경혈 범위 밖의 근거는 해당 항목 1점(유추)이 상한이다. 인용은 등록부 참조 ID(예: B3-17)로만 한다.",
]


def handle_get_layer_b_registry(args):
    category = (args.get("category") or "all").upper()
    ref_id = (args.get("reference_id") or "").strip().upper()
    query = (args.get("query") or "").strip().lower()
    reg = _cached("layer_b", lambda: _load_json("layer_b_json"))
    entries = reg.get("entries", [])
    if not entries:
        md = BACKEND.read_text("layer_b_md")
        return md or "⚠ Layer B 참조 등록부를 읽지 못했습니다."
    if ref_id:
        matched = [e for e in entries if e.get("id", "").upper() == ref_id]
    else:
        matched = []
        for e in entries:
            if category != "ALL" and e.get("tier", "").upper() != category:
                continue
            blob = " ".join(str(e.get(k) or "") for k in ("id", "type", "citation", "scope", "limits", "pmid", "doi", "year")).lower()
            if query and not all(t in blob for t in query.split()):
                continue
            matched.append(e)
    thr = reg.get("threshold", "8/12")
    out = [f"# 📚 [Layer B] 4계층 참조 등록부 (v{reg.get('version', '-')}, {reg.get('generated_at', '-')}) — {len(matched)}건",
           "", "**판정 규칙**", *[f"- {r.format(thr=thr)}" for r in BCHECK_RULE], ""]
    if not matched:
        out.append(f"조건(계층 {category}, ID {ref_id or '-'}, 검색어 {query or '-'})에 맞는 항목이 없습니다.")
        return "\n".join(out)
    out += ["| ID | 계층·유형 | 문헌 | 대상·범위 | B-Check 항목 | 한계 | 식별자·검증 |", "| :--- | :--- | :--- | :--- | :---: | :--- | :--- |"]
    for e in matched:
        ident = " ".join(x for x in (f"PMID {e['pmid']}" if e.get("pmid") else "", f"DOI {e['doi']}" if e.get("doi") else "") if x) or "—"
        out.append(f"| **{e.get('id')}** | {e.get('tier')} · {e.get('type', '')} | {e.get('citation', '')} | {e.get('scope', '')} | "
                   f"{e.get('bcheck_items', '')} | {e.get('limits', '-')} | {ident} ({e.get('verification', '-')}) |")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 도구 5: ARI v3.0 계산
# ---------------------------------------------------------------------------
STEPS = (0, 25, 50, 75, 100)
WEIGHTS = (0.40, 0.35, 0.25)


def _grade(x):
    return "A" if x >= 85 else "B" if x >= 70 else "C" if x >= 55 else "D"


def _fmt(x):
    return f"{x:.2f}".rstrip("0").rstrip(".")


def _rater_scores(args, suffix):
    def num(key):
        v = args.get(key + suffix)
        return None if v is None or v == "" else float(v)
    items = args.get("s_orig_items" + suffix)
    sc = {"s_orig": num("s_orig"), "s_clarity": num("s_clarity"), "s_reflex": num("s_reflex"), "s_safety": num("s_safety")}
    warnings = []
    if items:
        items = [float(x) for x in items]
        bad = [x for x in items if x not in STEPS]
        if len(items) != 4 or bad:
            warnings.append(f"S_orig 하위 4항목은 각각 0/25/50/75/100이어야 합니다(입력 {items}).")
        mean = sum(items) / len(items)
        if sc["s_orig"] is not None and abs(sc["s_orig"] - mean) > 0.01:
            warnings.append(f"S_orig {sc['s_orig']:g}가 하위 항목 평균 {mean:g}과 다릅니다 → 평균을 씁니다.")
        sc["s_orig"] = mean
    if all(v is None for v in sc.values()):
        return None, []
    missing = [k for k, v in sc.items() if v is None]
    if missing:
        warnings.append(f"누락: {', '.join(missing)}")
        return None, warnings
    for k in ("s_clarity", "s_reflex", "s_safety"):
        if sc[k] not in STEPS:
            warnings.append(f"{k} {sc[k]:g}은(는) 5단계 루브릭 값(0/25/50/75/100)이 아닙니다.")
    if not items and (sc["s_orig"] * 4) % 25:
        warnings.append(f"s_orig {sc['s_orig']:g}은(는) 하위 4항목 평균으로 나올 수 없는 값입니다(6.25 단위).")
    return sc, warnings


def handle_calculate_ari_v3_score(args):
    a, warn_a = _rater_scores(args, "")
    b, warn_b = _rater_scores(args, "_b")
    if a is None:
        return "⚠ 채점자 A 점수(s_orig, s_clarity, s_reflex, s_safety)를 모두 입력하세요. " + " ".join(warn_a)
    raters = [("A", a, warn_a)] + ([("B", b, warn_b)] if b else [])
    lac = args.get("layer_a_count")
    gate2 = lac is not None and int(lac) == 0
    out_rows, cores, equal, notes = [], [], [], []
    for name, sc, warns in raters:
        notes += [f"채점자 {name}: {w}" for w in warns]
        s_reflex = sc["s_reflex"]
        if gate2 and s_reflex > 25:
            notes.append(f"채점자 {name}: 게이트 2(Layer A 0편) → S_reflex {s_reflex:g} → 25")
            s_reflex = 25.0
        core = WEIGHTS[0] * sc["s_orig"] + WEIGHTS[1] * sc["s_clarity"] + WEIGHTS[2] * s_reflex
        eq = (sc["s_orig"] + sc["s_clarity"] + s_reflex) / 3
        cores.append(core)
        equal.append(eq)
        out_rows.append((name, sc["s_orig"], sc["s_clarity"], s_reflex, sc["s_safety"], core, eq))

    mean = sum(cores) / len(cores)
    half = (max(cores) - min(cores)) / 2
    eq_mean = sum(equal) / len(equal)
    si_vals = [r[4] for r in out_rows]
    si = sum(si_vals) / len(si_vals)
    mean_orig = sum(r[1] for r in out_rows) / len(out_rows)
    mean_clar = sum(r[2] for r in out_rows) / len(out_rows)
    gate1 = mean_orig < 50 or mean_clar < 50
    grade = _grade(mean)
    if gate1 and grade in ("A", "B"):
        grade = "C"
        notes.append("게이트 1(S_orig 또는 S_clarity 평균 < 50) → 최고 등급 C")
    gate3 = si <= 25
    tags = grade + ("·H" if gate2 else "")
    eq_grade = _grade(eq_mean)
    if gate1 and eq_grade in ("A", "B"):
        eq_grade = "C"
    sens = f"{eq_mean:.1f} ({eq_grade}, {'등급 불변' if eq_grade == grade else '가중치 민감'})"
    adjud = []
    if b:
        for k, label in (("s_orig", "S_orig"), ("s_clarity", "S_clarity"), ("s_reflex", "S_reflex"), ("s_safety", "SI")):
            if abs(a[k] - b[k]) >= 15:
                adjud.append(f"{label} (A {a[k]:g} / B {b[k]:g})")
    pm = f" ± {_fmt(half)}" if b else ""
    si_txt = _fmt(si) + (f" ± {_fmt((max(si_vals) - min(si_vals)) / 2)}" if b and max(si_vals) != min(si_vals) else "")
    notation = (f"ARI v3.0 | ARI-Core {_fmt(mean)}{pm} ({tags}){' | ⚠ 안전주의' if gate3 else ''} | SI {si_txt} | "
                f"잠정 가중치 0.40/0.35/0.25 | 민감도(등가중치): {sens}")

    out = ["# 📊 ARI v3.0 계산 결과", "", f"`{notation}`", ""]
    if not b:
        out.append("- **단일 채점 → '예비'** 표지(Tier 2). Tier 3는 독립 채점자 2인의 이중 채점(`*_b` 입력)이 필요하다.")
    out += ["", "| 채점자 | S_orig (0.40) | S_clarity (0.35) | S_reflex (0.25) | SI | ARI-Core | 등가중치 |", "| :---: | :---: | :---: | :---: | :---: | :---: | :---: |"]
    for name, so, scl, sr, ss, core, eq in out_rows:
        out.append(f"| {name} | {_fmt(so)} | {_fmt(scl)} | {_fmt(sr)} | {_fmt(ss)} | {_fmt(core)} | {_fmt(eq)} |")
    out += ["", "## 게이트",
            f"- 게이트 1 (S_orig·S_clarity 평균 < 50 → 최고 C): {'⚠ 적용' if gate1 else '미적용'}",
            f"- 게이트 2 (Layer A 0편 → S_reflex ≤ 25 + H): {'⚠ 적용' if gate2 else ('미적용' if lac is not None else '⚠ 미판정 — layer_a_count를 입력하세요')}",
            f"- 게이트 3 (SI ≤ 25 → ⚠ 안전주의): {'⚠ 적용' if gate3 else '미적용'}",
            "", "## 판정",
            f"- 등급: **{grade}** (A ≥ 85 · B 70~84 · C 55~69 · D < 55)" + (f" · 구간 [{_fmt(min(cores))}, {_fmt(max(cores))}]" if b else ""),
            f"- 이중 채점 조정 필요(하위 점수 차 ≥ 15): {', '.join(adjud)}" if adjud else ("- 이중 채점 조정 필요 항목 없음" if b else "")]
    if notes:
        out += ["", "## 입력 점검", *[f"- {n}" for n in notes]]

    targets = args.get("targets") or []
    if len(targets) >= 2:
        out += ["", "## Tri-Target 분기 판정 (ΔARI-Core ≥ 10 그리고 ± 구간 비중첩일 때만 우위)"]
        ts = sorted(({"name": t.get("name", "?"), "core": float(t.get("ari_core", 0)), "half": float(t.get("half_range", 0))} for t in targets),
                    key=lambda t: -t["core"])
        top = ts[0]
        verdicts = []
        for t in ts[1:]:
            d = top["core"] - t["core"]
            overlap = (top["core"] - top["half"]) <= (t["core"] + t["half"])
            win = d >= 10 and not overlap
            verdicts.append(win)
            out.append(f"- {top['name']} {_fmt(top['core'])} ± {_fmt(top['half'])} vs {t['name']} {_fmt(t['core'])} ± {_fmt(t['half'])}: "
                       f"Δ {_fmt(d)}, 구간 {'겹침' if overlap else '비중첩'} → {'우위' if win else '우위 아님(병기)'}")
        if all(verdicts):
            out.append(f"- **결론: {top['name']} 단독 우위**")
        else:
            losers = [t["name"] for t, w in zip(ts[1:], verdicts) if w]
            ties = [t["name"] for t, w in zip(ts[1:], verdicts) if not w]
            out.append(f"- **결론: {' ≈ '.join([top['name']] + ties)}" + (f" > {', '.join(losers)}" if losers else "") + "**")
    return "\n".join(x for x in out if x is not None)


# ---------------------------------------------------------------------------
# 도구 6: 정본 프로토콜
# ---------------------------------------------------------------------------
FRAMEWORK_SECTIONS = {
    "sources": [r"^## .*1\.\s*핵심 목적"],
    "tiers": [r"^## .*2\.\s*질문"],
    "ranks": [r"^## .*3\.\s*작업 순위"],
    "rank0": [r"^### \[Rank 0\]"],
    "rank1_2": [r"^### \[Rank 1"],
    "rank3": [r"^### \[Rank 3\]"],
    "rank4": [r"^### \[Rank 4\]"],
    "rank5": [r"^### \[Rank 5\]"],
    "rank6": [r"^### \[Rank 6\]"],
    "rank7": [r"^### \[Rank 7\]"],
    "b_check": [r"^### \[Rank 6\]"],
    "rubrics": [r"^## .*4\.\s*ARI", r"^### \[Rank 7\]"],
    "components": [r"^## .*5\.\s*최종 보고서"],
    "history": [r"^## .*6\.\s*문서 이력"],
}


def _md_section(lines, pattern):
    for i, line in enumerate(lines):
        if re.match(pattern, line):
            lv = len(line) - len(line.lstrip("#"))
            for j in range(i + 1, len(lines)):
                lj = len(lines[j]) - len(lines[j].lstrip("#"))
                if 0 < lj <= lv and lines[j][lj:lj + 1] == " ":
                    return "\n".join(lines[i:j]).strip()
            return "\n".join(lines[i:]).strip()
    return None


def handle_get_framework_protocol(args):
    section = (args.get("section") or "summary").strip().lower()
    text = framework_text()
    if not text:
        return "⚠ 프레임워크 정본을 읽지 못했습니다."
    head = f"> 정본: Framework {framework_version()} ({BACKEND.label})"
    if section == "all":
        return head + "\n\n" + text
    lines = text.splitlines()
    if section == "summary":
        heads = [l for l in lines if re.match(r"^#{2,3} ", l)]
        return head + "\n\n# 정본 목차\n" + "\n".join(f"- {h.lstrip('#').strip()}" for h in heads) + \
            "\n\n`section`으로 " + ", ".join(sorted(FRAMEWORK_SECTIONS)) + ", all 중 하나를 고르세요."
    pats = FRAMEWORK_SECTIONS.get(section)
    if not pats:
        return f"⚠ 알 수 없는 section: {section}. 사용 가능: summary, all, " + ", ".join(sorted(FRAMEWORK_SECTIONS))
    parts = [_md_section(lines, p) for p in pats]
    found = [p for p in parts if p]
    if not found:
        return f"⚠ 정본에서 '{section}' 절을 찾지 못했습니다(제목이 바뀌었을 수 있음). section='summary'로 목차를 확인하세요."
    return head + "\n\n" + "\n\n".join(found)


# ---------------------------------------------------------------------------
# 도구 7: 4대 원전 검색 (search_classic_records)
# ---------------------------------------------------------------------------
KEY_SUBSECTIONS = ("部位", "定位", "简要结语")
DEFAULT_MAX_CHARS = 14000


def _books():
    return BACKEND.classics_books()


def _section_book(kind, key):
    return kind == "extra" or key in ("穴位通鉴", "腧穴通考")


def _lines(dir_id, name):
    ver = BACKEND.classics_version(dir_id, name) if hasattr(BACKEND, "classics_version") else None
    key = ("lines", dir_id, name, ver)
    got = _CACHE.get(key)
    if got is None:
        raw = (BACKEND.classics_read(dir_id, name) or "").splitlines()
        norm = [norm_text(l) for l in raw]
        got = (raw, norm, [compact(l) for l in norm])
        if raw:
            _CACHE[key] = got
    return got


def _hlevel(line):
    n = len(line) - len(line.lstrip("#"))
    return n if n and line[n:n + 1] == " " else 0


def _title(line):
    return re.sub(r"<a id=[^>]*></a>", "", line.lstrip("#")).strip()


def _heading_name(line):
    """'#### 足三里 Zúsānlǐ ST 36' · '### （三十六）足三里 …' · '#### 10. 三里二穴' → '足三里' / '三里'"""
    body = _title(line)
    body = re.sub(r"^（[^）]*）", "", body)
    body = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", body).strip()
    tok = body.split()[0] if body else ""
    tok = re.sub(r"(?<=..)[一二三四五六]?穴$", "", tok)
    return tok


def _code_regex(code):
    m = re.match(r"^([A-Z]{2})-?0*(\d+)$", (code or "").upper().replace(" ", ""))
    if m:
        return re.compile(rf"\b{m.group(1)}\s?0?{int(m.group(2))}\b")
    if re.match(r"^EX-[A-Z]+\d+$", (code or "").upper()):
        return re.compile(rf"\b{re.escape(code.upper())}\b")
    return None


def _point_terms(acupoint):
    """경혈 입력 → (코드, 레코드, 정식 혈명 목록, 별명 목록) — 모두 간체"""
    p = resolve_point(acupoint)
    if p:
        names = [norm_text(p["name_cn"])]
        aliases = [norm_text(a.strip()) for a in re.split(r"[,、，;/]", p.get("aliases_hanja", ""))
                   if re.fullmatch(r"[\u3400-\u9fff]{2,6}", a.strip())]  # '-'·'.' 같은 빈칸 표지 제외
        return p["code"], p, names, aliases
    raw = acupoint.strip()
    if _code_regex(raw):
        return raw.upper(), None, [], []
    return "", None, [norm_query(raw)], []


def _short_names(names):
    """足三里→三里, 手三里→三里처럼 수족 접두를 뗀 약칭(동의보감 등 조선 문헌 제목용)"""
    return [n[1:] for n in names if len(n) >= 3 and n[0] in "手足"]


def _find_section(dir_id, code, names, meridian_key, require_meridian):
    code_re = _code_regex(code) if code else None
    files = BACKEND.classics_list(dir_id)
    preferred = [f for f in files if meridian_key and meridian_key in norm_text(f)]
    rest = [f for f in files if f not in preferred]
    for min_lv in (3, 1):  # 경혈 장은 ###·#### 수준. 파일 제목(#·##)의 코드 오적중을 피한다
        for group in (preferred, rest):
            BACKEND.classics_prefetch(dir_id, group)
            for fname in group:
                raw, norm, _ = _lines(dir_id, fname)
                for i, line in enumerate(norm):
                    lv = _hlevel(line)
                    if not lv or lv < min_lv or lv > 4:
                        continue
                    by_code = bool(code_re and code_re.search(line))
                    by_name = bool(names) and _heading_name(line) in names
                    if not (by_code or by_name):
                        continue
                    if by_name and not by_code and require_meridian and meridian_key:
                        ctx = norm_text(fname) + "".join(norm[k] for k in range(i) if 0 < _hlevel(norm[k]) < lv)[-400:]
                        if meridian_key not in ctx:
                            continue  # 다른 경맥의 같은 이름 혈(예: 手阳明 '三里')
                    end = len(raw)
                    for j in range(i + 1, len(raw)):
                        lj = _hlevel(norm[j])
                        if lj and lj <= lv:
                            end = j
                            break
                    return fname, i, end
    return None


def _aliases_from_section(dir_id, sec, own):
    """《穴位通鉴》 '二. 别名' 소절의 인용문에서 별명을 뽑는다"""
    fname, s, e = sec
    raw, norm, _ = _lines(dir_id, fname)
    out = []
    for i in range(s + 1, e):
        if _hlevel(norm[i]) and "别名" in norm[i]:
            lv = _hlevel(norm[i])
            for k in range(i + 1, e):
                if 0 < _hlevel(norm[k]) <= lv:
                    break
                for q in re.findall(r"“([^”]+)”", norm[k]):
                    q = re.sub(r"^(\d+\.)?\s*", "", q)
                    for tok in re.split(r"[、，,；;。.]|一名|又名|亦名|别名", q):
                        tok = tok.strip()
                        if re.fullmatch(r"[\u4e00-\u9fff]{2,5}", tok) and tok not in own and tok not in out:
                            out.append(tok)
            break
    return out


def _alias_ok(line_c, alias, own_names, others):
    """별명이 다른 혈명(예: '三里' ⊂ '手三里')의 일부로만 나오면 적중으로 치지 않는다"""
    start = 0
    while True:
        k = line_c.find(alias, start)
        if k < 0:
            return False
        inside_other = False
        for n in others:
            if n in own_names or alias not in n or n == alias:
                continue
            off = n.find(alias)
            if line_c[max(0, k - off):k - off + len(n)] == n:
                inside_other = True
                break
        if not inside_other:
            return True
        start = k + 1


def _snippet(raw, norm, terms, width=130):
    pos = min([norm.find(t) for t in terms if t and norm.find(t) >= 0] or [0])
    a, b = max(0, pos - width), min(len(raw), pos + width)
    return ("…" if a else "") + raw[a:b].strip() + ("…" if b < len(raw) else "")


def _match_at(comp, i, terms):
    """i행 단독 또는 i·i+1행 이어 붙인 문자열에 모든 검색어가 있으면 (True, 이어짐 여부)"""
    if all(t in comp[i] for t in terms):
        return True, False
    if i + 1 < len(comp) and comp[i + 1] and not all(t in comp[i + 1] for t in terms):
        joined = comp[i] + comp[i + 1]
        if all(t in joined for t in terms) and comp[i]:
            return True, True
    return False, False


def _front_matter(fname):
    return bool(re.search(r"_0{1,3}_|目录|目錄|索引|序|凡例|编写说明|書名|书名", fname))


def handle_search_classic_records(args):
    acupoint = (args.get("acupoint") or "").strip()
    query = (args.get("query") or "").strip()
    book_filter = (args.get("classic_book") or "all").strip()
    use_aliases = args.get("include_aliases", True) is not False

    def intarg(k, d, lo, hi):
        try:
            return max(lo, min(int(args.get(k) or d), hi))
        except (TypeError, ValueError):
            return d
    limit = intarg("limit", 10, 1, 50)
    excerpt_chars = intarg("excerpt_chars", 1200, 200, 4000)
    max_chars = intarg("max_chars", DEFAULT_MAX_CHARS, 3000, 40000)

    if not acupoint and not query:
        return "⚠ `acupoint`(경혈 코드·혈명) 또는 `query`(검색어) 가운데 하나 이상을 입력하세요. 예: acupoint='ST36', query='两筋间'"
    fkey = norm_query(book_filter)
    books = [b for b in _books() if fkey in ("all", norm_text(b[0]))]  # 키도 같은 규칙(번체·이체자 접기)으로 맞춰 비교
    if not books:
        return "⚠ 알 수 없는 원전 필터: " + book_filter + ". 사용 가능: all, " + ", ".join(b[0] for b in _books())
    if not any(BACKEND.classics_list(b[1]) for b in books):
        return f"⚠ 원전 코퍼스를 읽을 수 없습니다 ({BACKEND.label})."

    terms = [compact(norm_query(t)) for t in query.split()] if query else []
    terms = [t for t in terms if t]
    code, prec, names, aliases = _point_terms(acupoint) if acupoint else ("", None, [], [])
    meridian_key = MERIDIAN_KEYS.get((prec["code"] if prec else code)[:2].upper()) if (prec or code) else None
    title = f"{prec['code']} {prec['name_kr']}/{prec['name_cn']}" if prec else (f"'{acupoint}'" if acupoint else "")

    blocks = []
    sections = {}
    if acupoint:  # 혈위별 장 찾기 → 정식 혈명·별명 보강
        for key, dir_id, label, kind in books:
            if _section_book(kind, key):
                cand = names + (_short_names(names) + aliases if kind == "extra" else [])
                sec = _find_section(dir_id, code, cand, meridian_key, require_meridian=(kind == "extra"))
                if sec:
                    sections[key] = sec
                    if not names:
                        names = [_heading_name(_lines(dir_id, sec[0])[1][sec[1]])]
                    if key == "穴位通鉴":
                        aliases += [a for a in _aliases_from_section(dir_id, sec, names) if a not in aliases]
    alias_list = list(dict.fromkeys(a for a in (aliases + _short_names(names)) if a and a not in names)) if use_aliases else []
    others = all_point_names()

    for key, dir_id, label, kind in books:
        blk = [f"## {label}"]
        sec = sections.get(key)
        if acupoint and _section_book(kind, key) and sec:
            fname, s, e = sec
            raw, norm, comp = _lines(dir_id, fname)
            lv0 = _hlevel(norm[s])
            blk.append(f"- **경혈 장**: `{fname}` L{s + 1}–{e} — {_title(raw[s])[:80]}")
            subs = [(i, _title(raw[i])) for i in range(s + 1, e) if _hlevel(norm[i]) > lv0]
            if subs:
                blk.append("- **소절**: " + " · ".join(f"{t} (L{i + 1})" for i, t in subs[:20]))
            if terms:
                hits = []
                for i in range(s, e):
                    ok, span = _match_at(comp[:e], i, terms)
                    if ok:
                        hits.append((i, span))
                blk.append(f"- **검색어 적중** {len(hits)}건" + (f" (상위 {limit}건)" if len(hits) > limit else ""))
                for i, span in hits[:limit]:
                    text = raw[i] + (" ⏎ " + raw[i + 1] if span else "")
                    blk.append(f"  - L{i + 1}{'–' + str(i + 2) if span else ''}: {_snippet(text, norm_text(text), terms)}")
            else:
                targets = [(i, t) for i, t in subs if any(k in norm_text(t) for k in KEY_SUBSECTIONS)]
                if not targets:  # 소절이 없는 장(동의보감 등)은 장 전체를 발췌
                    targets = [(s, _title(raw[s]))]
                for i, t in targets:
                    lv = _hlevel(norm[i])
                    j = next((k for k in range(i + 1, e) if 0 < _hlevel(norm[k]) <= lv), e)
                    blk.append(f"\n### {t} (L{i + 1}–{j})")
                    size = 0
                    for line in raw[i + 1:j]:
                        x = re.sub(r"<a id=[^>]*></a>", "", line).strip()
                        if not x or x.startswith((">", "![", "〔p.")):
                            continue
                        blk.append(x)
                        size += len(x)
                        if size >= excerpt_chars:
                            blk.append("…(생략)")
                            break
            blocks.append(blk)
            continue
        if acupoint and _section_book(kind, key) and kind != "extra":
            blk.append(f"- 해당 경혈 장을 찾지 못했습니다 (코드 {code or '-'}, 혈명 {', '.join(names) or '-'}).")
            blocks.append(blk)
            continue

        # 행 단위 검색: 편별 원전, 또는 장을 찾지 못한 보조 문헌, 또는 경혈 미지정
        files = BACKEND.classics_list(dir_id)
        BACKEND.classics_prefetch(dir_id, files)
        if not terms and not names and not alias_list:
            blk.append("- 혈명을 확정하지 못해 검색하지 않았습니다. `query`를 함께 입력하세요.")
            blocks.append(blk)
            continue
        found, seen = [], set()
        for fname in files:
            raw, norm, comp = _lines(dir_id, fname)
            for i in range(len(comp)):
                if not comp[i]:
                    continue
                span = False
                if terms:
                    ok, span = _match_at(comp, i, terms)
                    if not ok:
                        continue
                via_alias = False
                if names or alias_list:
                    window = "".join(comp[max(0, i - 1):i + (3 if span else 2)]) if terms else comp[i] + (comp[i + 1] if span else "")
                    if any(n in window for n in names):
                        pass
                    elif alias_list and any(_alias_ok(window, a, names, others) for a in alias_list):
                        via_alias = True
                    else:
                        continue
                key_txt = comp[i] + (comp[i + 1] if span else "")
                if key_txt in seen:
                    continue
                seen.add(key_txt)
                score = (4 if any(n in comp[i] for n in names) else 0) + (0 if via_alias else 1) \
                    + (1 if not fname.endswith("_한글번역.md") else 0) - (3 if _front_matter(fname) else 0) \
                    + sum(comp[i].count(t) for t in terms)
                found.append((score, fname, i, span, via_alias))
        found.sort(key=lambda x: (-x[0], files.index(x[1]), x[2]))
        n_tr = sum(1 for f in found if f[1].endswith("_한글번역.md"))
        n_alias = sum(1 for f in found if f[4])
        must = terms or names
        blk.append(f"- **적중** {len(found)}건 (검색: {' + '.join(must + (['별명 ' + '/'.join(alias_list)] if alias_list and not terms else []))})"
                   + (f" · 한글번역 {n_tr}건" if n_tr else "") + (f" · 별명 적중 {n_alias}건" if n_alias else "")
                   + (f" · 관련도순 상위 {limit}건" if len(found) > limit else ""))
        for score, fname, i, span, via_alias in found[:limit]:
            raw, norm, _ = _lines(dir_id, fname)
            text = raw[i] + (" ⏎ " + raw[i + 1] if span else "")
            tags = (" [한글번역]" if fname.endswith("_한글번역.md") else "") + (" [별명]" if via_alias else "")
            blk.append(f"  - `{fname}`{tags} L{i + 1}{'–' + str(i + 2) if span else ''}: {_snippet(text, norm_text(text), must or alias_list)}")
        blocks.append(blk)

    head = [
        f"# 📜 고전문헌 검색: {title}{' · ' if title and query else ''}{('검색어 ' + repr(query)) if query else ''}",
        f"- **원전**: {', '.join(b[2] for b in books)} · **원전별 최대** {limit}건 · 번체/간체·이체자 통합 · 행 경계·문장부호 무시",
    ]
    if acupoint:
        head.append(f"- **혈명**: {', '.join(names) or '-'}" + (f" · **별명**: {', '.join(alias_list)}" if alias_list else "")
                    + (" (별명 적중은 [별명]으로 표시, 같은 이름의 다른 혈일 수 있음)" if alias_list else ""))
    tail = ["", "> 행 번호는 각 원전 정제 마크다운 기준. 《证治通鉴》은 원문을 기준 텍스트로 하고 같은 편 `_한글번역`과 대조한다(정본 Rank 1 & 2)."]
    text = "\n".join(head + [""] + ["\n".join(b) + "\n" for b in blocks] + tail)
    if len(text) <= max_chars:
        return text
    # 길이 제한: 원전별 블록을 비례해 줄인다(행 단위)
    budget = max_chars - len("\n".join(head + tail)) - 200
    total = sum(len("\n".join(b)) for b in blocks)
    trimmed = []
    for b in blocks:
        share = max(800, int(budget * len("\n".join(b)) / total))
        keep, size = [], 0
        for line in b:
            if size + len(line) > share:
                keep.append("…(길이 제한으로 생략 — `classic_book`·`limit`·`query`·`max_chars`로 조절)")
                break
            keep.append(line)
            size += len(line) + 1
        trimmed.append(keep)
    return "\n".join(head + [""] + ["\n".join(b) + "\n" for b in trimmed] + tail)


# ---------------------------------------------------------------------------
# 도구 정의 · JSON-RPC 루프
# ---------------------------------------------------------------------------
def tool_definitions():
    book_keys = ["all"] + [b[0] for b in _books()]
    return [
        {"name": "get_acupoint_anatomy_profile",
         "description": "경혈 데이터 프로파일: 마스터 CSV(경락·KJH 이명·출전), 2대 교재(공통교재·김재효) 근육·신경·혈관 비교, 문헌별 자침 깊이(푼→2.3mm 환산, 0=금침), 통합 생의학 DB 요약(역색인 편수·DB 기재 반사 회로), 기존 Tier 3 보고서와 ARI 표기. 층차 배치·Tri-Target·ARI 값은 만들지 않는다.",
         "inputSchema": {"type": "object", "properties": {"acupoint": {"type": "string", "description": "경혈 코드(ST36, LU5, CV12) 또는 혈명(족삼리, 足三里)"}}, "required": ["acupoint"]}},
        {"name": "get_fma_anatomy_profile",
         "description": "FMA 5.1.0 해부 실체 프로파일: 교재 용어↔FMA:ID 대응 수준, (로컬 FMA 색인이 있으면) 신경 지배·상위 줄기 사슬·척수 분절 합집합(B-Check ②), 2대 교재 FMA 비교.",
         "inputSchema": {"type": "object", "properties": {"acupoint": {"type": "string", "description": "경혈 코드 또는 혈명"},
                                                          "format": {"type": "string", "enum": ["markdown", "json"], "description": "출력 형식(기본 markdown)"}}, "required": ["acupoint"]}},
        {"name": "search_biomedical_reflex_db",
         "description": "Layer A 통합 생의학 마스터 DB 검색. 경혈 코드·혈명이면 랜드마크·역색인·검출 혈위로 정확히 대조하고, 그 밖의 검색어는 모든 단어가 제목·초록·키워드·MeSH에 있는 논문을 찾는다. duplicate·missing·superseded는 기본 제외. 설계(인체·동물·리뷰)는 제목·초록 키워드 추정값.",
         "inputSchema": {"type": "object", "properties": {
             "query": {"type": "string", "description": "경혈 코드·혈명(ST36, 족삼리) 또는 키워드(vagal adrenal, TRPV1)"},
             "evidence_filter": {"type": "string", "enum": ["all", "human", "animal", "review", "mechanism"], "description": "설계 필터(키워드 추정 기반, 기본 all)"},
             "include_inactive": {"type": "boolean", "description": "인용 제외 상태 논문도 보이기(기본 false)"},
             "limit": {"type": "integer", "description": "최대 결과 수(기본 10, 최대 50)"}}, "required": ["query"]}},
        {"name": "get_layer_b_registry",
         "description": "Layer B 4계층 참조 등록부(B1 해부학·B2 반사생리·B3 침구 기전·B4 근막/기계신호)와 B-Check 판정 규칙(6항목 각 0~2점, 합계 ≥ 8/12 그리고 ①·② ≥ 1).",
         "inputSchema": {"type": "object", "properties": {
             "category": {"type": "string", "enum": ["all", "B1", "B2", "B3", "B4"]},
             "reference_id": {"type": "string", "description": "참조 ID (예: B3-17)"},
             "query": {"type": "string", "description": "키워드(모든 단어 포함), 예: vagal, Langevin fascia"}}}},
        {"name": "calculate_ari_v3_score",
         "description": "ARI v3.0 계산(정본 Rank 7·4절): ARI-Core = 0.40·S_orig + 0.35·S_clarity + 0.25·S_reflex, SI 분리, 게이트 1~3, 등급 A~D, 등가중치 민감도. 채점자 B 점수(*_b)를 주면 이중 채점(평균 ± 반범위, 15점 이상 차이 조정 표시), targets를 주면 Tri-Target 우위 판정(ΔARI ≥ 10·구간 비중첩). 루브릭 값(0/25/50/75/100)이 아니면 경고.",
         "inputSchema": {"type": "object", "properties": {
             "s_orig": {"type": "number", "description": "채점자 A S_orig(하위 4항목 평균)"},
             "s_orig_items": {"type": "array", "items": {"type": "number"}, "description": "채점자 A S_orig 하위 4항목(각 0/25/50/75/100)"},
             "s_clarity": {"type": "number"}, "s_reflex": {"type": "number"}, "s_safety": {"type": "number", "description": "SI"},
             "s_orig_b": {"type": "number"}, "s_orig_items_b": {"type": "array", "items": {"type": "number"}},
             "s_clarity_b": {"type": "number"}, "s_reflex_b": {"type": "number"}, "s_safety_b": {"type": "number"},
             "layer_a_count": {"type": "integer", "description": "해당 위치를 특정한 Layer A 논문 편수(0이면 게이트 2). 입력하지 않으면 게이트 2 미판정"},
             "targets": {"type": "array", "description": "Tri-Target 비교용 [{name, ari_core, half_range}]",
                         "items": {"type": "object", "properties": {"name": {"type": "string"}, "ari_core": {"type": "number"}, "half_range": {"type": "number"}}}}},
             "required": ["s_orig", "s_clarity", "s_reflex", "s_safety"]}},
        {"name": "search_classic_records",
         "description": "4대 원전(《中国针灸穴位通鉴》·《针灸腧穴通考》·《中国针灸证治通鉴》·《中国针灸经络通鉴》)과 설정된 보조 문헌(예: 《東醫寶鑑》)의 정제 코퍼스를 직접 검색한다. acupoint: 혈위별 장(파일·행 범위·소절)과 부위/定位·简要结语 발췌, 편별 원전에서는 혈명·별명 행(관련도순, 원문·번역 중복 제거). query: 모든 검색어가 든 행(행 경계·문장부호 무시, 번체/간체·이체자 통합).",
         "inputSchema": {"type": "object", "properties": {
             "acupoint": {"type": "string", "description": "경혈 코드 또는 혈명 (ST36, EX-HN3, 족삼리, 足三里, 百会)"},
             "query": {"type": "string", "description": "원문 검색어. 공백으로 나누면 모든 단어 포함 (예: '兩筋間', '针入 五分')"},
             "classic_book": {"type": "string", "enum": book_keys, "description": "특정 원전만 (기본 all)"},
             "include_aliases": {"type": "boolean", "description": "별명(三里·下陵 등)으로도 찾기(기본 true, [별명] 표시)"},
             "limit": {"type": "integer", "description": "원전별 최대 적중 수(기본 10, 최대 50)"},
             "excerpt_chars": {"type": "integer", "description": "경혈 장 소절 발췌 길이(기본 1200)"},
             "max_chars": {"type": "integer", "description": "응답 최대 길이(기본 14000, 최대 40000)"}}}},
        {"name": "get_framework_protocol",
         "description": "로직 정본(acupoint_anatomical_logic_framework.md)의 해당 절을 제목 기준으로 잘라 돌려준다. 기본 summary(목차). sources·tiers·ranks·rank0~rank7·b_check·rubrics·components·history·all.",
         "inputSchema": {"type": "object", "properties": {"section": {"type": "string", "enum": ["summary", "all"] + sorted(FRAMEWORK_SECTIONS)}}}},
    ]


HANDLERS = {
    "get_acupoint_anatomy_profile": handle_get_acupoint_anatomy_profile,
    "get_fma_anatomy_profile": handle_get_fma_anatomy_profile,
    "search_biomedical_reflex_db": handle_search_biomedical_reflex_db,
    "get_layer_b_registry": handle_get_layer_b_registry,
    "calculate_ari_v3_score": handle_calculate_ari_v3_score,
    "search_classic_records": handle_search_classic_records,
    "get_framework_protocol": handle_get_framework_protocol,
}


def call_tool(name, arguments):
    fn = HANDLERS.get(name)
    if not fn:
        raise ValueError(f"Unknown tool: {name}")
    token = BACKEND.cache_token() if hasattr(BACKEND, "cache_token") else None
    if token != _CACHE.get("__token__"):  # 원격: TTL이 지나면 파싱한 데이터를 버린다(원전 행 캐시는 파일 SHA로 따로 관리)
        for k in [k for k in _CACHE if not (isinstance(k, tuple) and k[0] == "lines")]:
            del _CACHE[k]
        _CACHE["__token__"] = token
    return fn(arguments or {})


def _send(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def run_stdio(backend):
    """MCP stdio JSON-RPC 루프"""
    set_backend(backend)
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception as e:
            sys.stderr.write(f"[acupoint-core] invalid JSON: {e}\n")
            continue
        rid, method, params = req.get("id"), req.get("method"), req.get("params") or {}
        if rid is None:  # 알림(notifications/*)에는 응답하지 않는다
            continue
        try:
            if method == "initialize":
                _send({"jsonrpc": "2.0", "id": rid, "result": {
                    "protocolVersion": params.get("protocolVersion") if params.get("protocolVersion") in SUPPORTED_PROTOCOLS else PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION}}})
            elif method == "tools/list":
                _send({"jsonrpc": "2.0", "id": rid, "result": {"tools": tool_definitions()}})
            elif method == "tools/call":
                text = call_tool(params.get("name"), params.get("arguments"))
                _send({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": str(text)}]}})
            elif method == "ping":
                _send({"jsonrpc": "2.0", "id": rid, "result": {}})
            else:
                _send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Method not found: {method}"}})
        except BaseException as e:  # SystemExit 포함 — 한 도구의 실패가 서버 전체를 끝내지 않게 한다
            if isinstance(e, KeyboardInterrupt):
                raise
            _send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32000, "message": f"{type(e).__name__}: {e}"}})


# ----- remote_backend.py -----
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


REMOTE_DATA_PATHS = {
    "framework": "framework/acupoint_anatomical_logic_framework.md",
    "layer_b_md": "framework/layer_b_reference_registry.md",
    "layer_b_json": "data/layer_b_reference_registry.json",
    "master_csv": "data/361_Acupoints_Refined_Master_DB_v2.csv",
    "biomed_json": "data/경혈_생의학_신경반사_마스터DB.json",
    "fma_json": "data/acupoint_fma_mapping.json",
    "reference_json": "data/mcp_reference_data.json",
}
REMOTE_BOOKS = [
    ("穴位通鉴", "中国针灸穴位通鉴", "《中国针灸穴位通鉴》"),
    ("腧穴通考", "针灸腧穴通考", "《针灸腧穴通考》"),
    ("证治通鉴", "中国针灸证治通鉴", "《中国针灸证治通鉴》"),
    ("经络通鉴", "中国针灸经络通鉴", "《中国针灸经络通鉴》"),
]


class RemoteBackend:
    def __init__(self, repo, branch, token="", cache_dir=None, ttl=3600):
        self.repo, self.branch, self.token, self.ttl = repo, branch, token, max(60, int(ttl))
        self.label = f"GitHub {repo}@{branch}"
        self.cache_dir = Path(cache_dir or os.environ.get("ACUPOINT_CACHE_DIR") or (Path.home() / ".acupoint_anatomy" / "cache"))
        (self.cache_dir / "classics").mkdir(parents=True, exist_ok=True)
        self._mem = {}        # 경로 → (받은 시각, 내용)
        self._index = None    # (받은 시각, {원전 디렉토리: {파일명: sha1}})

    # --- HTTP -----------------------------------------------------------
    def _get(self, url, accept=None):
        headers = {"User-Agent": "AcupointAnatomy-Remote-MCP/3.0"}
        if accept:
            headers["Accept"] = accept
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as resp:
            return resp.read()

    def _raw(self, path):
        url = f"https://raw.githubusercontent.com/{self.repo}/{urllib.parse.quote(self.branch)}/{urllib.parse.quote(path)}"
        return self._get(url).decode("utf-8", errors="replace")

    def fetch(self, path, ttl=None):
        ttl = self.ttl if ttl is None else ttl
        hit = self._mem.get(path)
        if hit and time.time() - hit[0] < ttl:
            return hit[1]
        try:
            text = self._raw(path)
        except Exception as e:
            sys.stderr.write(f"[remote] {path} 받기 실패: {e}\n")
            return hit[1] if hit else ""  # 실패 시 이전 내용 유지
        self._mem[path] = (time.time(), text)
        return text

    # --- 백엔드 인터페이스 ------------------------------------------------
    def cache_token(self):
        """이 값이 바뀌면 코어가 파싱해 둔 데이터를 버리고 다시 읽는다"""
        return int(time.time() // self.ttl)

    def read_text(self, key):
        path = REMOTE_DATA_PATHS.get(key)
        return self.fetch(path) if path else ""

    def _books_index(self):
        if self._index and time.time() - self._index[0] < self.ttl:
            return self._index[1]
        books = {}
        text = self.fetch("data/classics/index.json")
        if text:
            try:
                for d, files in json.loads(text).get("books", {}).items():
                    books[d] = {f["name"]: f.get("sha1") for f in files}
            except Exception as e:
                sys.stderr.write(f"[remote] index.json 파싱 실패: {e}\n")
        if not books:  # 색인이 없으면 GitHub API로 목록만(SHA 없음)
            for _, d, _ in REMOTE_BOOKS:
                try:
                    url = f"https://api.github.com/repos/{self.repo}/contents/{urllib.parse.quote('data/classics/' + d)}?ref={urllib.parse.quote(self.branch)}"
                    items = json.loads(self._get(url, "application/vnd.github+json").decode("utf-8"))
                    books[d] = {i["name"]: None for i in items if i.get("type") == "file" and i.get("name", "").endswith(".md")}
                except Exception as e:
                    sys.stderr.write(f"[remote] {d} 목록 실패: {e}\n")
        if books:
            self._index = (time.time(), books)
        return books

    def classics_books(self):
        idx = self._books_index()
        return [(k, d, label, "core") for k, d, label in REMOTE_BOOKS if not idx or d in idx]

    def classics_list(self, dir_id):
        return sorted(self._books_index().get(dir_id, {}))

    def classics_version(self, dir_id, name):
        return self._books_index().get(dir_id, {}).get(name)

    def classics_read(self, dir_id, name):
        sha = self.classics_version(dir_id, name)
        disk = self.cache_dir / "classics" / f"{sha}.md" if sha else None
        if disk and disk.exists():
            return disk.read_text(encoding="utf-8")
        try:
            text = self._raw(f"data/classics/{dir_id}/{name}")
        except Exception as e:
            sys.stderr.write(f"[remote] {dir_id}/{name} 받기 실패: {e}\n")
            return ""
        if disk:
            got = hashlib.sha1(text.encode("utf-8").replace(b"\r\n", b"\n")).hexdigest()
            if got == sha:  # 색인과 내용이 맞을 때만 디스크에 남긴다
                disk.write_text(text, encoding="utf-8", newline="\n")
        return text

    def classics_prefetch(self, dir_id, names):
        todo = [n for n in names if not (self.classics_version(dir_id, n) and
                                         (self.cache_dir / "classics" / f"{self.classics_version(dir_id, n)}.md").exists())]
        if len(todo) > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=8) as ex:
                list(ex.map(lambda n: self.classics_read(dir_id, n), todo))

    def fma_instance(self):
        return None, None


def main():
    ap = argparse.ArgumentParser(description="Acupoint Anatomy Remote MCP Server (GitHub streaming)")
    ap.add_argument("--repo", default=os.getenv("GITHUB_REPO", "jaehyokim-sketch/acupoint_anatomy"))
    ap.add_argument("--branch", default=os.getenv("GITHUB_BRANCH", "main"))
    ap.add_argument("--token", default=os.getenv("GITHUB_TOKEN", ""), help="GitHub PAT (공개 저장소는 불필요)")
    ap.add_argument("--cache-dir", default=None, help="디스크 캐시 위치 (기본 ~/.acupoint_anatomy/cache)")
    ap.add_argument("--ttl", type=int, default=3600, help="데이터 재확인 주기(초, 기본 3600)")
    args, _ = ap.parse_known_args()
    run_stdio(RemoteBackend(args.repo, args.branch, args.token, args.cache_dir, args.ttl))


if __name__ == "__main__":
    main()

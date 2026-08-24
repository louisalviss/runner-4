import json,re,sys
from urllib.parse import urljoin,urlparse
from pathlib import Path
from cloakbrowser import launch

TARGETS=[
(8,'PitchGround','https://pitchground.com','https://seoengine.ai/submit'),
(17,'AI Database','https://www.ai-database.org','https://ai-database.org/submit'),
(21,'All Things AI','https://allthings-ai.com','https://allthings-ai.com/submit'),
(24,'App Stacks','https://appstacks.club','https://appstacks.club/submit'),
(34,'GitHub (awesome lists)','https://github.com','https://github.com/submit'),
(38,'Indie Page','https://indiepa.ge','https://indiepa.ge/submit'),
(40,'Launch Space','https://launchspace.io','https://launchspace.io/submit'),
(43,'Makerlog (Projects section)','https://getmakerlog.com','https://ambitiousfounder.com/submit'),
(46,'No Code List','https://nocodelist.co','https://nocodelist.co/submit'),
(50,'SaaS Discovery','https://saasdiscovery.com','https://saasdiscovery.com/submit-startup'),
(53,'Side Project Ideas','https://sideprojectideas.com','https://sideprojectideas.com/submit'),
(59,'Tiny Alternatives','https://tinyalternatives.com','https://tinyalternatives.com/submit'),
(66,'Active Search Results','https://www.activesearchresults.com','https://www.activesearchresults.com/submit'),
(71,'AIFindr','https://aifindr.com','https://aifindr.com/submit'),
(77,'AppVault','https://appvault.io','https://appvault.io/submit'),
(80,"Ben's Bites",'https://news.bensbites.com','https://www.bensbites.com/submit'),
(82,'BestofAI','https://bestofai.com','https://bestofai.com/submit'),
(84,'Brownbook','https://www.brownbook.net','https://www.brownbook.net/submit'),
(87,'BuiltWithTools','https://builtwithtools.com','https://builtwithtools.com/submit'),
(88,'BusinessHunt','https://businesshunt.co','https://businesshunt.co/submit'),
(95,'DR Checker','https://drchecker.org','https://drchecker.org/submit'),
(105,'IndieLaunch','https://indielaunch.co','https://indielaunch.ai/submit'),
(111,'kj123.cn','https://www.kj123.cn','https://goodpics.net/submit'),
(124,'LaunchTab','https://launchtab.com','https://www.atom.com/submit'),
(131,'Makerlist.io','https://makerlist.io','https://makerlist.io/submit-startup'),
(139,'NextGen Tools','https://www.nxgntools.com','https://www.nxgntools.com/submit'),
(148,'ProductBurst','https://productburst.com','https://bubble.io/submit'),
(149,'ProductCatalog','https://productcatalog.io','https://productcatalog.io/submit'),
(155,'ProjectHunt','https://projecthunt.me','https://projecthunt.me/submit'),
(157,'Ramen.Tools','https://ramen.tools','https://ramen.tools/submit'),
(158,'SaaS Arena','https://saasarena.com','https://championleadership.com/submit'),
(164,'SaaS Launch','https://saaslaunch.io','https://saaslaunch.io/submit'),
(166,'SaaS Pages','https://saaspages.xyz','https://saaspages.xyz/submit'),
(172,'SaaSFrame','https://saasframe.io','https://www.saasframe.io/submit'),
(176,'SaaSPick','https://saaspick.com','https://saaspick.com/submit'),
(184,'Sitelike.org','https://www.sitelike.org','https://www.sitelike.org/submit'),
(200,'StartupLister','https://startuplister.com','https://bubble.io/submit'),
(201,'StartupNow','https://startupnow.co','https://startupnow.co/submit'),
(216,'TinyLaunch','https://www.tinylaunch.com','https://www.tinylaunch.com/submit'),
(229,'Tools For Makers','https://toolsformakers.com','https://globalpande.ru.com/submit'),
(232,'ToolScout','https://toolscout.app','https://toolscout.app/submit'),
(239,'VerifiedDR','https://verifieddr.com','https://verifieddr.com/submit')]

STRONG=re.compile(r'(submit(\s+(a|your))?\s*(tool|product|startup|project|site|software|app)?|add\s+(your\s+)?(tool|product|startup|project|listing|software|app)|get\s+listed|list\s+(your\s+)?(product|startup|tool|software|app)|suggest\s+new\s+(application|app|tool)|vendor\s+portal|claim\s+(your\s+)?(business|profile|listing)|launch\s+(your\s+)?(product|project)|create\s+(a\s+)?(product|company|listing|profile))',re.I)
LOGIN=re.compile(r'(log[ -]?in|sign[ -]?in|sign[ -]?up|create (an |your )?account|continue with (google|github|apple)|authentication required)',re.I)
NEG=re.compile(r'(share|news|blog|article|advertis|affiliate|facebook|twitter|linkedin|reddit|press|contact us|newsletter)',re.I)
CHALLENGES=('just a moment','attention required','verify you are human','verifying connection','checking your browser','access denied','security verification','prove your humanity','blocked by network security')
COMMON=['/submit','/submit/','/submit-tool','/submit-a-tool','/submit-product','/submit-startup','/add-listing','/add-your-product','/add-product','/get-listed','/suggest','/launch','/launchpad','/vendor','/vendors','/dashboard']

def host(u):
    h=urlparse(u).netloc.lower().split(':')[0]
    return h[4:] if h.startswith('www.') else h

def same_host(a,b):
    x,y=host(a),host(b)
    return x==y or x.endswith('.'+y) or y.endswith('.'+x)

def run_worker(wid,workers,outfile):
    mine=[t for i,t in enumerate(TARGETS) if i%workers==wid]
    browser=launch(browser_version='146.0.7680.177.5',headless=False,humanize=True)
    def visit(url,extract=False):
        p=browser.new_page(viewport={'width':1365,'height':768})
        try:
            resp=p.goto(url,wait_until='domcontentloaded',timeout=15000); p.wait_for_timeout(850)
            text=p.locator('body').inner_text(timeout=5000); title=p.title(); status=resp.status if resp else 0; final=p.url
            low=(title+' '+text[:9000]).lower(); ch=next((x for x in CHALLENGES if x in low),None); forms=p.locator('form').count()
            links=[]
            if extract:
                try:
                    for a in p.locator('a').all():
                        href=a.get_attribute('href') or ''; label=(a.inner_text(timeout=500) or '').strip(); blob=label+' '+href
                        if href and STRONG.search(blob) and not NEG.search(blob): links.append({'url':urljoin(final,href).split('#')[0],'text':label[:120]})
                except Exception: pass
            return {'url':url,'http':status,'final':final,'title':title[:180],'chars':len(text),'ok':bool(status and 200<=status<400 and not ch and len(text)>80),'challenge':ch,'forms':forms,'login_signal':bool(LOGIN.search(low)),'strong_signal':bool(STRONG.search(title+' '+text[:7000])),'sample':' '.join(text.split())[:500],'links':links[:20],'error':''}
        except Exception as e:
            return {'url':url,'http':0,'final':'','title':'','chars':0,'ok':False,'challenge':None,'forms':0,'login_signal':False,'strong_signal':False,'sample':'','links':[],'error':type(e).__name__+': '+str(e)[:240]}
        finally:
            try:p.close()
            except:pass
    rows=[]
    try:
        for row,name,home,old in mine:
            hp=visit(home,True); op=visit(old); cands=[]; seen=set()
            for x in hp.get('links',[]):
                if same_host(x['url'],home) and x['url'] not in seen: seen.add(x['url']); cands.append(x)
            if hp.get('ok'):
                base=f"{urlparse(hp['final']).scheme}://{urlparse(hp['final']).netloc}"
                for path in COMMON:
                    u=base+path
                    if u not in seen: seen.add(u); cands.append({'url':u,'text':'generated '+path})
            def score(x):
                q=(x['text']+' '+x['url']).lower(); s=0
                for k,w in [('submit',10),('get-listed',9),('add-your',9),('add-',7),('suggest',7),('vendor',6),('launchpad',6),('launch',5),('claim',5),('dashboard',2)]:
                    if k in q:s+=w
                return -s
            probes=[]
            for x in sorted(cands,key=score)[:7]:
                v=visit(x['url']); v['anchor_text']=x['text']; probes.append(v)
            viable=[]
            for v in probes:
                if not v.get('ok') or not same_host(v.get('final') or v['url'],home): continue
                blob=v.get('anchor_text','')+' '+v.get('final','')+' '+v.get('title','')+' '+v.get('sample','')
                if STRONG.search(blob) or v.get('forms',0)>0: viable.append(v)
            old_valid=op.get('ok') and same_host(op.get('final') or old,home) and (op.get('strong_signal') or op.get('forms',0)>0 or op.get('login_signal'))
            if old_valid:
                best=op; cls='AUTH_REQUIRED' if op.get('login_signal') and not op.get('forms') else 'OPEN'
            elif viable:
                best=viable[0]; authish=best.get('login_signal') and (re.search(r'(login|signin|signup|auth|account)',best.get('final',''),re.I) or not best.get('strong_signal')); cls='AUTH_REQUIRED' if authish else 'OPEN'
            elif hp.get('challenge') or op.get('challenge'): best=None; cls='BLOCKED'
            elif not hp.get('ok'): best=None; cls='DEAD_OR_UNREACHABLE'
            else: best=None; cls='STALE'
            rows.append({'row':row,'name':name,'home':home,'old':old,'classification':cls,'best_route':(best or {}).get('final',''),'homepage_probe':hp,'old_route_probe':op,'candidate_probes':probes})
    finally: browser.close()
    Path(outfile).write_text(json.dumps(rows,ensure_ascii=False,indent=2))

if __name__=='__main__': run_worker(int(sys.argv[1]),int(sys.argv[2]),sys.argv[3])

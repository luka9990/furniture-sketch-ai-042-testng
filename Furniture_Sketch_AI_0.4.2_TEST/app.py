import io
import json
import uuid
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
import extra_streamlit_components as stx
from i18n import LANGUAGES, tr

st.set_page_config(page_title='Furniture Sketch AI 0.4.2', page_icon='📐', layout='wide')
KINDS=['Ormar','Polica / regal','Komoda','Kuhinjski element','Sto']
DEFAULTS={'Ormar':(1200,2000,600),'Polica / regal':(900,1800,350),'Komoda':(1000,850,450),'Kuhinjski element':(600,720,560),'Sto':(1200,750,650)}

def new_item(kind='Ormar'):
    w,h,d=DEFAULTS[kind]
    return {'id':uuid.uuid4().hex[:12], 'name':'Element 1', 'kind':kind, 'w':w,'h':h,'d':d,'t':18,'x':0,'y':0,'z':0,'bays':[w-36], 'shelves':[2], 'doors':2 if kind=='Ormar' else 0, 'back':True, 'back_t':3, 'back_mode':'Spoljašnja (naliježuća)', 'front_mode':'Naklapajuća', 'front_t':18, 'front_reveal':2, 'leg_enabled':kind=='Kuhinjski element', 'kitchen_type':'Donji element', 'legs':100, 'top_t':38, 'countertop':False, 'gap':2, 'material_price':0.0, 'notes':''}

def new_project():
    return {'format':'furniture-sketch-ai','version':'0.4.2','name':'__DEFAULT_PROJECT__','items':[],'unit':'mm'}

def validate_project(raw):
    if not isinstance(raw,dict) or raw.get('format')!='furniture-sketch-ai' or not isinstance(raw.get('items'),list):
        raise ValueError('Ovo nije podržana datoteka projekta.')
    if len(raw['items'])>100: raise ValueError('Projekat ima previše elemenata (maksimalno 100).')
    result=new_project(); result['name']=str(raw.get('name','__DEFAULT_PROJECT__'))[:100]
    result['unit']=raw.get('unit') if raw.get('unit') in ('mm','cm') else 'mm'
    result['items']=[]; ids=set()
    for old in raw['items']:
        if not isinstance(old,dict): continue
        kind=old.get('kind','Ormar')
        if kind not in KINDS: continue
        item=new_item(kind)
        for key in ('name','w','h','d','t','x','y','z','bays','shelves','doors','back','back_t','back_mode','front_mode','front_t','front_reveal','leg_enabled','kitchen_type','legs','top_t','countertop','gap','material_price','notes'):
            if key in old: item[key]=old[key]
        for key in ('w','h','d','t'):
            item[key]=float(item[key]);
            if not (0 < item[key] <= 100000): raise ValueError('Neispravne dimenzije u projektu.')
        for key in ('x','y','z','legs','top_t','back_t','front_t','front_reveal','gap','material_price'):
            item[key]=float(item[key]);
            if abs(item[key])>1000000: raise ValueError('Neispravan broj u projektu.')
        item['bays']=[float(v) for v in item['bays'][:12]] if isinstance(item['bays'],list) else []
        item['shelves']=[max(0,min(25,int(v))) for v in item['shelves'][:12]] if isinstance(item['shelves'],list) else []
        item['doors']=max(0,min(8,int(item['doors'])))
        item['id']=uuid.uuid4().hex[:12]
        item['name']=str(item['name'])[:100]; item['notes']=str(item['notes'])[:3000]
        result['items'].append(item)
    return result

if 'project_data' not in st.session_state:
    st.session_state.project_data=new_project()
if 'selected_item' not in st.session_state:
    st.session_state.selected_item=(st.session_state.project_data['items'][0]['id'] if st.session_state.project_data['items'] else None)
P=st.session_state.project_data

if 'ui_language' not in st.session_state:
    st.session_state.ui_language='bs'
# Browser-side cookie manager; only the consent preference is stored by this app.
# No analytics or advertising cookies are installed.
cookie_manager=stx.CookieManager(key='fsa_cookie_manager')
consent_from_browser=cookie_manager.get('fsa_consent_v1')
if 'privacy_choice' not in st.session_state:
    st.session_state.privacy_choice=consent_from_browser if consent_from_browser in ('accept','reject') else None
lang=st.session_state.ui_language
T=lambda key: tr(key,lang)
def display_project_name(name):
    return T('Moj projekat') if name in ('__DEFAULT_PROJECT__','Moj projekat') else (T('Novi projekat') if name=='__NEW_PROJECT__' else name)
def stored_project_name(name):
    return T('Moj projekat') if name=='__DEFAULT_PROJECT__' else (T('Novi projekat') if name=='__NEW_PROJECT__' else name)


# No optional tracking cookies are set by this application. This is a session-only
# preference; Streamlit/platform essential cookies are outside the app's control.
@st.dialog('🍪 Cookies / Kolačići', dismissible=False)
def privacy_dialog():
    st.write('Furniture Sketch AI does not use advertising or analytics cookies. '
             'Streamlit and its hosting provider may use essential cookies for sessions and security. '
             'This choice applies to optional cookies controlled by this app only; currently there are none.')
    c1,c2=st.columns(2)
    with c1:
        if st.button('Reject optional cookies / Odbij',use_container_width=True):
            cookie_manager.set('fsa_consent_v1','reject',key='consent_reject',max_age=31536000,secure=True,same_site='lax'); st.session_state.privacy_choice='reject'; st.rerun()
    with c2:
        if st.button('Allow optional cookies / Prihvati',use_container_width=True):
            cookie_manager.set('fsa_consent_v1','accept',key='consent_accept',max_age=31536000,secure=True,same_site='lax'); st.session_state.privacy_choice='accept'; st.rerun()

@st.dialog('🌍 Choose your language / Odaberi jezik', dismissible=False)
def language_dialog():
    chosen=st.selectbox('Language / Jezik',list(LANGUAGES),format_func=lambda v:LANGUAGES[v],
                        index=list(LANGUAGES).index(st.session_state.ui_language))
    if st.button(tr('Potvrdi jezik',chosen),use_container_width=True):
        st.session_state.ui_language=chosen
        st.session_state.language_settings=chosen
        st.session_state.language_selected=True
        st.rerun()

if st.session_state.privacy_choice is None:
    privacy_dialog()
elif not st.session_state.get('language_selected',False):
    language_dialog()


def item_label(ident, items, translate):
    for item in items:
        if item['id']==ident:
            name=item['name']
            kind=translate(item['kind'])
            if name.strip().lower() in (item['kind'].lower(),kind.lower()):
                return kind
            return f"{translate('Element')} {name.split()[-1]} — {kind}" if name.startswith('Element ') and name[8:].isdigit() else f'{name} — {kind}'
    return ident

def display_columns(lang):
    return {key:tr(key,lang) for key in ('Dio','Komada','Dužina (mm)','Širina (mm)','Debljina (mm)','Napomena','Element')}
def localized_parts(parts):
    rows=[]
    for part in parts:
        r=dict(part)
        if 'Dio' in r:
            name=r['Dio']
            if name.startswith('Polica odjeljka '):
                name=T('Polica odjeljka')+' '+name.split()[-1]
            r['Dio']=T(name)
        if r.get('Napomena'): r['Napomena']=T(r['Napomena'])
        rows.append(r)
    return rows
def localized_warning(w):
    if w.startswith('Zbir širina odjeljaka mora biti '):
        import re
        nums=re.findall(r'\d+\.\d+',w)
        if len(nums)==2:return f"{T('Zbir širina odjeljaka mora biti')} {nums[0]} mm; {T('trenutno je')} {nums[1]} mm."
    return T(w)

def add_part(parts,name,qty,a,b,thick,note=''):
    if qty>0 and a>0 and b>0:
        parts.append({'Dio':name,'Komada':int(qty),'Dužina (mm)':round(a,2),'Širina (mm)':round(b,2),'Debljina (mm)':round(thick,2),'Napomena':note})

def calculate(item):
    parts=[]; warnings=[]
    w,h,d,t=[float(item[k]) for k in ('w','h','d','t')]
    kind=item['kind']
    if min(w,h,d,t)<=0: return [],['Sve dimenzije moraju biti veće od nule.']
    if kind in KINDS[:4]:
        legs=float(item.get('legs',0)) if item.get('leg_enabled',kind=='Kuhinjski element' and item.get('kitchen_type')=='Donji element') else 0
        top=float(item.get('top_t',38)) if kind=='Kuhinjski element' and item.get('countertop') else 0
        corpus_h=h-legs-top
        doors=int(item.get('doors',0))
        front_t=float(item.get('front_t',18)) if doors else 0
        front_reveal=float(item.get('front_reveal',2)) if doors else 0
        # The entered depth is the finished outside depth, including fronts and their reveal.
        corpus_d=d-front_t-front_reveal
        if corpus_h<=2*t or corpus_d<=0: return [],['Nema mjesta za odjeljke pri zadanim dimenzijama.']
        bays=item.get('bays',[]); n=len(bays)
        if not n:return [],['Dodaj barem jedan odjeljak.']
        inner=w-(n+1)*t
        if inner<=0:return [],['Nema mjesta za odjeljke pri zadanim dimenzijama.']
        if abs(sum(bays)-inner)>0.1:warnings.append(f'Zbir širina odjeljaka mora biti {inner:.1f} mm; trenutno je {sum(bays):.1f} mm.')
        add_part(parts,'Bočna stranica',2,corpus_h,corpus_d,t)
        add_part(parts,'Gornja ploča',1,w-2*t,corpus_d,t)
        add_part(parts,'Donja ploča',1,w-2*t,corpus_d,t)
        add_part(parts,'Vertikalna pregrada',n-1,corpus_h-2*t,corpus_d,t)
        for i,bay in enumerate(bays):
            shelves=item.get('shelves',[])
            add_part(parts,f'Polica odjeljka {i+1}',shelves[i] if i<len(shelves) else 0,bay,corpus_d,t,'Provjeriti montažu i potrebne zazore')
        if item.get('back'):
            mode=item.get('back_mode','Spoljašnja (naliježuća)')
            if mode=='Upadajuća falcana':
                bw=w-18; bh=corpus_h-2
                note='Falcana leđa: širina korpusa − 18 mm; visinu i falc provjeriti prema izvedbi'
            elif mode=='Unutrašnja':
                bw=w-2*t; bh=corpus_h-2*t
                note='Unutrašnja leđa između stranica; provjeriti utor i dubinu nalijeganja'
            else:
                bw=w-2; bh=corpus_h-2
                note='Neupadajuća leđa: širina i visina korpusa − 2 mm'
            if bh<=0 or bw<=0: warnings.append('Dimenzije leđa nisu moguće za odabranu konstrukciju.')
            add_part(parts,'Leđa',1,bh,bw,float(item.get('back_t',3)),note)
        if doors:
            gap=float(item.get('gap',2)); front_mode=item.get('front_mode','Naklapajuća')
            fw=w if front_mode=='Naklapajuća' else w-2*t
            fh=corpus_h if front_mode=='Naklapajuća' else corpus_h-2*t
            dw=(fw-(doors+1)*gap)/doors
            if dw<=0 or fh-2*gap<=0: warnings.append('Dimenzije fronte nisu moguće za zadani zazor i broj vrata.')
            add_part(parts,'Vrata / fronta',doors,fh-2*gap,dw,front_t,'Približno; preklop i šarke provjeriti prema okovu')
        if legs>0: warnings.append('Nogice su uračunate u ukupnu visinu; nisu uključene u krojnu listu ploča.')
        if kind=='Komoda':warnings.append('Ladice i vodilice nisu automatski proračunate.')
        if kind=='Kuhinjski element':
            kt=item.get('kitchen_type','Donji element')
            if kt=='Donji element' and item.get('countertop'):
                add_part(parts,'Radna ploča',1,w,d,float(item.get('top_t',38)),'Provjeriti prepuste i spojeve')
            elif kt=='Viseći (gornji) element':warnings.append('Obavezno provjeriti nosivost zida i sistem vješanja.')
    elif kind=='Sto':
        add_part(parts,'Ploča stola',1,w,d,t)
        add_part(parts,'Noga stola (pojednostavljeno)',4,h-t,60,60,'Presjek noge 60 × 60 mm; provjeriti stabilnost')
        warnings.append('Spojevi, nosivost i stabilnost stola nisu projektovani.')
    if any(float(p['Dužina (mm)'])<=0 or float(p['Širina (mm)'])<=0 for p in parts):warnings.append('Neke dimenzije su neispravne.')
    return parts,warnings

def actual_bounds(it):
    x,y,z=[float(it[k]) for k in ('x','y','z')]
    height=float(it['h'])
    # Height entered by the user is already the finished overall height, including legs.
    return (x,x+float(it['w']),y,y+height,z,z+float(it['d']))

st.title('📐 Furniture Sketch AI')
with st.sidebar.expander('🌍 '+T('Postavke jezika i privatnosti')):
    selected_lang=st.selectbox(T('Jezik'),list(LANGUAGES),format_func=lambda v:LANGUAGES[v],index=list(LANGUAGES).index(lang),key='language_settings')
    if selected_lang != lang:
        st.session_state.ui_language=selected_lang; st.rerun()
    st.caption(T('Kolačići: neobavezni dozvoljeni') if st.session_state.privacy_choice=='accept' else T('Kolačići: neobavezni odbijeni'))
    if st.button('🍪 '+T('Kolačići i privatnost')):
        st.session_state.privacy_choice=None; st.rerun()
st.caption('Furniture Sketch AI 0.4.2 · '+T('Verzija 0.4 · više jezika · više elemenata · izvoz projekata'))
st.info(T('Proračuni su preliminarni. Prije izrade provjeri okove, spojeve, zazore, nosivost i stvarne mjere.'))

with st.sidebar:
    st.header('📁 '+T('Projekat'))
    project_name_display=display_project_name(P['name'])
    if st.session_state.get('_project_name_lang') != lang:
        if P['name'] in ('__DEFAULT_PROJECT__','Moj projekat','__NEW_PROJECT__'):
            st.session_state.project_name_widget=project_name_display
        st.session_state._project_name_lang=lang
    entered_name=st.text_input(T('Naziv projekta'),value=project_name_display,key='project_name_widget')
    P['name'] = P['name'] if (P['name'] in ('__DEFAULT_PROJECT__','Moj projekat','__NEW_PROJECT__') and entered_name==project_name_display) else entered_name
    P['unit']=st.selectbox(T('Jedinica prikaza'),['mm','cm'],index=['mm','cm'].index(P['unit']))
    uploaded=st.file_uploader(T('Otvori spremljeni projekat (.json)'),type=['json'],key='open_project')
    if uploaded is not None:
        try:
            raw=json.loads(uploaded.getvalue().decode('utf-8'))
            st.session_state.pending_project=validate_project(raw)
            st.success(T('Datoteka je spremna za učitavanje.'))
        except (ValueError,TypeError,UnicodeDecodeError,OverflowError) as exc:
            st.error(f"{T('Neuspješno učitavanje')}: {exc}")
    if 'pending_project' in st.session_state and st.button(T('Učitaj projekat (zamijeni trenutni)'),use_container_width=True):
        st.session_state.project_data=st.session_state.pop('pending_project')
        items=st.session_state.project_data['items']
        st.session_state.selected_item=items[0]['id'] if items else None
        st.rerun()
    st.download_button('💾 '+T('Sačuvaj projekat (.json)'),json.dumps({**P,'name':stored_project_name(P['name'])},ensure_ascii=False,indent=2).encode('utf-8'),file_name='furniture_projekat.json',mime='application/json',use_container_width=True)
    if st.button(T('Novi prazan projekat'),use_container_width=True):
        st.session_state.project_data={'format':'furniture-sketch-ai','version':'0.4.2','name':'__NEW_PROJECT__','items':[],'unit':'mm'}
        st.session_state.selected_item=None; st.rerun()
    st.caption(T('Trenutno se projekti spremaju kao datoteke. Google Drive povezivanje još nije aktivno.'))

items=P['items']; scale=10 if P['unit']=='cm' else 1; unit=P['unit']

def dimension(label,old,key,minimum=0.0):
    value=st.number_input(f'{label} ({unit})',min_value=float(minimum)/scale,value=max(float(old),float(minimum))/scale,step=1.0 if unit=='mm' else 0.1,key=key)
    return round(value*scale,4)

tab_editor,tab_layout,tab_summary=st.tabs(['🛠️ '+T('Elementi i dimenzije'),'📏 '+T('Raspored i razmaci'),'📋 '+T('Ukupna krojna lista')])
with tab_editor:
    a,b=st.columns([2,1])
    with a:
        if items:
            ids=[i['id'] for i in items]
            if st.session_state.selected_item not in ids: st.session_state.selected_item=ids[0]
            selected=st.selectbox(T('Odaberi element'),ids,index=ids.index(st.session_state.selected_item),format_func=lambda ident: item_label(ident,items,T))
            st.session_state.selected_item=selected
        else: selected=None; st.info(T('Projekat je prazan. Dodaj prvi element.'))
    with b:
        new_kind=st.selectbox(T('Vrsta novog elementa'),KINDS,format_func=T)
        if st.button('➕ '+T('Dodaj element'),use_container_width=True):
            item=new_item(new_kind); item['name']=f'Element {len(items)+1}'
            items.append(item); st.session_state.selected_item=item['id']; st.rerun()
    if selected:
        item=next(i for i in items if i['id']==selected)
        col1,col2=st.columns([3,1])
        with col1: item['name']=st.text_input(T('Naziv elementa'),item['name'],key=f'name_{selected}')
        with col2:
            if st.button('📄 '+T('Dupliraj'),use_container_width=True):
                clone=json.loads(json.dumps(item)); clone['id']=uuid.uuid4().hex[:12]; clone['name']=item['name']+' '+T('(kopija)')
                items.append(clone); st.session_state.selected_item=clone['id']; st.rerun()
            if st.button('🗑️ '+T('Ukloni'),use_container_width=True):
                items.remove(item); st.session_state.selected_item=items[0]['id'] if items else None; st.rerun()
        dims=st.columns(4)
        for col,key,label in zip(dims,['w','h','d','t'],[T('Širina'),T('Visina'),T('Dubina'),T('Debljina materijala')]):
            with col: item[key]=dimension(label,item[key],f'{selected}_{key}',1)
        if item['kind'] in KINDS[:4]:
            st.subheader(T('Odjeljci — svaki može biti druge širine'))
            n=st.number_input(T('Broj odjeljaka'),min_value=1,max_value=12,value=max(1,len(item['bays'])),key=f'n_{selected}')
            if n!=len(item['bays']):
                inner=max(0,item['w']-(n+1)*item['t'])
                item['bays']=[round(inner/n,3)]*n
                item['shelves']=[2]*n
            available=item['w']-(n+1)*item['t']
            st.caption(f"{T('Ukupna čista širina za odjeljke')}: **{available/scale:.1f} {unit}** {T('(nakon bočnih stranica i pregrada).')}")
            if st.button(T('Podijeli na jednake širine'),key=f'equal_{selected}'):
                item['bays']=[round(available/n,4)]*n
                for i in range(n): st.session_state[f'bay_{selected}_{i}']=item['bays'][i]/scale
                st.rerun()
            for i in range(n):
                c1,c2=st.columns(2)
                with c1: item['bays'][i]=dimension(f"{T('Čista širina odjeljka')} {i+1}",item['bays'][i],f'bay_{selected}_{i}',0)
                with c2: item['shelves'][i]=st.number_input(f"{T('Police u odjeljku')} {i+1}",min_value=0,max_value=25,value=int(item['shelves'][i]),key=f'shelf_{selected}_{i}')
            diff=sum(item['bays'])-available
            if abs(diff)>0.1: st.warning(f"{T('Širine odjeljaka se ne uklapaju: razlika')} {diff/scale:+.2f} {unit}.")
            item['back']=st.checkbox(T('Dodaj leđa'),value=bool(item['back']),key=f'back_{selected}')
            if item['back']:
                bm=['Spoljašnja (naliježuća)','Unutrašnja','Upadajuća falcana']
                item['back_mode']=st.selectbox(T('Način montaže leđa'),bm,format_func=T,index=bm.index(item.get('back_mode')) if item.get('back_mode') in bm else 0,key=f'bm_{selected}')
                item['back_t']=dimension(T('Debljina leđa'),item['back_t'],f'backt_{selected}',1)
            if item['kind']!='Polica / regal':
                item['doors']=st.number_input(T('Broj vrata'),0,8,int(item['doors']),key=f'doors_{selected}')
                if item['doors']:
                    fm=['Naklapajuća','Upadajuća']
                    item['front_mode']=st.selectbox(T('Način ugradnje fronte'),fm,format_func=T,index=fm.index(item.get('front_mode')) if item.get('front_mode') in fm else 0,key=f'fm_{selected}')
                    item['front_t']=dimension(T('Debljina fronte'),item.get('front_t',18),f'ft_{selected}',1)
                    item['front_reveal']=dimension(T('Fuga ispred korpusa'),item.get('front_reveal',2),f'fr_{selected}',0)
                    item['gap']=dimension(T('Približni zazor vrata'),item['gap'],f'gap_{selected}',0)
            if item['kind']=='Kuhinjski element':
                kt=['Donji element','Viseći (gornji) element','Visoki element']
                item['kitchen_type']=st.selectbox(T('Tip kuhinjskog elementa'),kt,format_func=T,index=kt.index(item['kitchen_type']) if item['kitchen_type'] in kt else 0,key=f'kt_{selected}')
                if item['kitchen_type']=='Donji element':
                    item['leg_enabled']=True
                    item['countertop']=st.checkbox(T('Uključi radnu ploču'),bool(item['countertop']),key=f'ct_{selected}')
                    if item['countertop']: item['top_t']=dimension(T('Debljina radne ploče'),item['top_t'],f'topt_{selected}',1)
            item['leg_enabled']=st.checkbox(T('Element ima nogice'),value=bool(item.get('leg_enabled',False)),key=f'le_{selected}')
            if item['leg_enabled']:
                item['legs']=dimension(T('Visina nogica'),item.get('legs',100),f'legs_{selected}',0)
        else:
            st.caption(T('Za stol je dostupan preliminarni popis standardnih dijelova. Detaljni spojevi i okovi nisu obračunati.'))
        item['notes']=st.text_area(T('Bilješke uz element'),value=item['notes'],key=f'notes_{selected}',height=75)
        parts,warnings=calculate(item)
        st.subheader(T('Dijelovi ovog elementa'))
        if parts: st.dataframe(pd.DataFrame(localized_parts(parts)).rename(columns=display_columns(lang)),hide_index=True,use_container_width=True)
        for warning in warnings: st.warning(localized_warning(warning))

with tab_layout:
    st.write(T('Pozicije se mjere od zajedničke početne tačke projekta: **X = lijevo/desno, Y = visina od poda, Z = udaljenost od zida**. Svi brojevi su u istoj jedinici.'))
    for item in items:
        with st.expander(f"📦 {item['name']} ({T(item['kind'])})",expanded=len(items)<=3):
            cols=st.columns(3)
            for col,key,label in zip(cols,['x','y','z'],[T('X pozicija'),T('Y pozicija od poda'),T('Z pozicija')]):
                with col:
                    val=st.number_input(f'{label} ({unit})',value=float(item[key])/scale,step=1.0 if unit=='mm' else 0.1,key=f'pos_{item["id"]}_{key}')
                    item[key]=round(val*scale,4)
            bounds=actual_bounds(item)
            st.caption(f"{T('Raspon visine')}: {bounds[2]/scale:.1f}–{bounds[3]/scale:.1f} {unit}")
    if len(items)>=2:
        st.subheader(T('Međusobni razmaci'))
        pair_a,pair_b=st.columns(2)
        ids=[i['id'] for i in items]
        with pair_a: ia=st.selectbox(T('Prvi element'),ids,format_func=lambda v:next(i['name'] for i in items if i['id']==v),key='pair_a')
        with pair_b: ib=st.selectbox(T('Drugi element'),ids,index=1,format_func=lambda v:next(i['name'] for i in items if i['id']==v),key='pair_b')
        if ia==ib: st.info(T('Odaberi dva različita elementa.'))
        else:
            aa=actual_bounds(next(i for i in items if i['id']==ia)); bb=actual_bounds(next(i for i in items if i['id']==ib))
            def axis_gap(a0,a1,b0,b1): return max(a0-b1,b0-a1,0)
            gx=axis_gap(aa[0],aa[1],bb[0],bb[1]); gy=axis_gap(aa[2],aa[3],bb[2],bb[3]); gz=axis_gap(aa[4],aa[5],bb[4],bb[5])
            c1,c2,c3=st.columns(3)
            c1.metric(T('Horizontalni razmak X'),f'{gx/scale:.1f} {unit}')
            c2.metric(T('Vertikalni razmak Y'),f'{gy/scale:.1f} {unit}')
            c3.metric(T('Dubinski razmak Z'),f'{gz/scale:.1f} {unit}')
            if gx==gy==gz==0: st.warning(T('Prostorni rasponi elemenata se preklapaju ili dodiruju. Provjeri položaje.'))
            elif gy>0 and gx==0 and gz==0: st.success(f"{T('Elementi su jedan iznad drugog. Slobodan vertikalni razmak')}: {gy/scale:.1f} {unit}.")
            else: st.caption(T('Razmaci se mjere između vanjskih pravougaonih granica elemenata, ne između pojedinačnih vrata i okova.'))

with tab_summary:
    combined=[]; errors=[]; area=0.0
    for item in items:
        parts,warnings=calculate(item)
        for part in parts:
            part=dict(part); part={'Element':item['name'],**part}; combined.append(part)
            area+=part['Komada']*part['Dužina (mm)']*part['Širina (mm)']/1_000_000
        for warning in warnings: errors.append(f"{item['name']}: {warning}")
    c1,c2,c3=st.columns(3)
    c1.metric(T('Komada namještaja'),len(items)); c2.metric(T('Stavki krojne liste'),len(combined)); c3.metric(T('Površina dijelova'),f'{area:.2f} m²')
    if combined:
        df=pd.DataFrame(combined)
        st.dataframe(pd.DataFrame(localized_parts(combined)).rename(columns=display_columns(lang)),hide_index=True,use_container_width=True)
        st.download_button('📥 '+T('Preuzmi objedinjenu krojnu listu (CSV)'),df.to_csv(index=False).encode('utf-8-sig'),file_name='krojna_lista_projekta.csv',mime='text/csv')
    else: st.info(T('Dodaj elemente da dobiješ krojnu listu.'))
    for warning in errors: st.warning(localized_warning(warning))
    st.caption(T('Površina ne uključuje otpad pri rezanju, kantovanje ni stvarne cijene. Ovo nije optimizacija rezanja niti proizvodni nacrt.'))

st.divider()
st.caption('💾 '+T('Za nastavak na drugom uređaju preuzmi JSON projekta i otvori ga tamo. Google Drive sinhronizacija po računu zahtijeva zasebno OAuth podešavanje i nije uključena u ovoj probnoj verziji. Nema AI funkcija ni plaćanja.'))

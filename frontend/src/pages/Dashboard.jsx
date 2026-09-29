import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import useLiveUpdates from '../hooks/useLiveUpdates';
import { Activity, AlertTriangle, CalendarCheck2, Clock3, UsersRound, MessageSquareText, ArrowUpRight, Plus, Radio, PhoneCall, Send, CheckCircle2, UserPlus } from 'lucide-react';

export default function Dashboard(){
  const [stats,setStats]=useState(null);const [patients,setPatients]=useState([]);const [activity,setActivity]=useState([]);const [today,setToday]=useState({});const [showAdd,setShowAdd]=useState(false);const [lastEvent,setLastEvent]=useState('');
  const load=useCallback(async()=>{const [s,p,a,t]=await Promise.all([api.get('/dashboard/stats'),api.get('/patients'),api.get('/dashboard/activity'),api.get('/dashboard/today')]);setStats(s.data);setPatients(p.data);setActivity(a.data);setToday(t.data)},[]);
  const connected=useLiveUpdates(e=>{setLastEvent(e.type?.replaceAll('_',' ')||'Live update');load()});
  useEffect(()=>{load();const id=setInterval(load,12000);return()=>clearInterval(id)},[load]);
  const queue=useMemo(()=>[...patients].sort((a,b)=>rank(b)-rank(a)).slice(0,7),[patients]);
  return <div className="clinic-page">
    <header className="page-hero"><div><span className="eyebrow"><Radio size={13}/> {connected?'LIVE CLINIC WORKSPACE':'SYNCING WORKSPACE'}</span><h1>Follow-up operations</h1><p>Real-time patient recovery, conversations and care escalations.</p></div><div className="hero-actions"><div className="automation-pill"><span className="pulse-dot"></span><div><b>Automation active</b><small>{lastEvent||'Watching follow-up queue'}</small></div></div><button className="primary-small" onClick={()=>setShowAdd(true)}><UserPlus/>Add patient</button></div></header>

    <section className="metric-grid">
      <Metric icon={UsersRound} label="Active follow-ups" value={stats?.total_followups} tone="indigo" note="Across demo + real data"/>
      <Metric icon={Clock3} label="Due today" value={stats?.due_today} tone="blue" note={`${stats?.overdue||0} overdue`}/>
      <Metric icon={MessageSquareText} label="Response rate" value={`${stats?.response_rate||0}%`} tone="teal" note={`${stats?.responded||0} responded`}/>
      <Metric icon={AlertTriangle} label="Open escalations" value={today.open_escalations??stats?.escalations} tone="orange" note="Clinical + financial"/>
      <Metric icon={CalendarCheck2} label="Appointments" value={today.appointments_next_7_days??stats?.booked} tone="green" note="Next 7 days"/>
    </section>

    <div className="operations-grid">
      <section className="panel queue-panel"><div className="panel-head"><div><span>PRIORITY QUEUE</span><h2>Patients needing attention</h2></div><Link to="/patients">View all <ArrowUpRight/></Link></div><div className="queue-list">{queue.map(p=><Link to={`/patients/${p.id}`} className="queue-row" key={p.id}><div className={`queue-priority p-${p.priority?.toLowerCase()}`}></div><div className="avatar soft">{initials(p.name)}</div><div className="queue-copy"><b>{p.name}</b><span>{p.treatment}</span></div><div className="queue-status"><span className={`status-dot s-${p.follow_up_status?.toLowerCase()}`}></span>{pretty(p.follow_up_status)}</div><div className="queue-time">{when(p.follow_up_date)}</div><ArrowUpRight className="row-arrow"/></Link>)}</div></section>

      <section className="panel live-panel"><div className="panel-head"><div><span>LIVE AGENT ACTIVITY</span><h2>What the agent is doing</h2></div><div className={`live-light ${connected?'on':''}`}><i></i>{connected?'Live':'Syncing'}</div></div><div className="activity-feed">{activity.slice(0,11).map((a,i)=><div className="activity-item" key={`${a.type}-${a.patient_id}-${i}`}><div className={`activity-icon ${a.type==='TASK'?'task':a.direction==='INBOUND'?'in':'out'}`}>{a.type==='TASK'?<Activity/>:a.direction==='INBOUND'?<MessageSquareText/>:<Send/>}</div><div><b>{a.patient_name}</b><p>{a.text}</p><small>{a.channel||'SYSTEM'} · {pretty(a.status||'recorded')} · {timeAgo(a.at)}</small></div></div>)}</div></section>
    </div>

    <section className="workflow-band"><div><span className="eyebrow">AUTOMATION FLOW</span><h2>One workflow for demo and real patient data</h2></div><div className="workflow-steps">{[['1','Patient data','Added by staff or signup'],['2','Follow-up task','Scheduled automatically'],['3','Outreach','SMS / voice / web'],['4','Agent response','Intent + context'],['5','Clinic action','Book or escalate']].map(([n,t,d])=><div key={n}><i>{n}</i><span><b>{t}</b><small>{d}</small></span></div>)}</div></section>
    {showAdd&&<QuickPatientModal close={()=>setShowAdd(false)} done={()=>{setShowAdd(false);load()}}/>}
  </div>
}

function QuickPatientModal({close,done}){const [f,setF]=useState({name:'',phone:'',email:'',treatment:'Root Canal',treatment_status:'Emergency pain relief completed',preferred_channel:'SMS',follow_up_date:''});const [saving,setSaving]=useState(false);const submit=async e=>{e.preventDefault();setSaving(true);try{await api.post('/patients',{...f,last_visit:new Date().toISOString(),follow_up_date:f.follow_up_date?new Date(f.follow_up_date).toISOString():null});done()}finally{setSaving(false)}};return <div className="modal-backdrop"><form className="modal-card" onSubmit={submit}><div className="modal-head"><div><span className="eyebrow">NEW CARE JOURNEY</span><h2>Add a patient</h2><p>A follow-up task is created automatically. Blank follow-up time = about one minute from now.</p></div><button type="button" onClick={close}>×</button></div><div className="form-grid"><label>Patient name<input required value={f.name} onChange={e=>setF({...f,name:e.target.value})}/></label><label>Phone<input value={f.phone} onChange={e=>setF({...f,phone:e.target.value})}/></label><label>Email<input type="email" value={f.email} onChange={e=>setF({...f,email:e.target.value})}/></label><label>Channel<select value={f.preferred_channel} onChange={e=>setF({...f,preferred_channel:e.target.value})}><option>SMS</option><option>VOICE</option></select></label><label className="wide">Treatment<input value={f.treatment} onChange={e=>setF({...f,treatment:e.target.value})}/></label><label className="wide">Treatment status<input value={f.treatment_status} onChange={e=>setF({...f,treatment_status:e.target.value})}/></label><label className="wide">Follow-up date/time<input type="datetime-local" value={f.follow_up_date} onChange={e=>setF({...f,follow_up_date:e.target.value})}/></label></div><div className="modal-actions"><button type="button" className="secondary-cta" onClick={close}>Cancel</button><button className="primary-cta compact" disabled={saving}>{saving?'Creating…':<><Plus/>Create & start automation</>}</button></div></form></div>}
function Metric({icon:Icon,label,value,tone,note}){return <div className={`metric-card ${tone}`}><div className="metric-icon"><Icon/></div><div><span>{label}</span><b>{value??'—'}</b><small>{note}</small></div></div>}
function rank(p){return (p.priority==='URGENT'?50:p.priority==='HIGH'?30:p.priority==='MEDIUM'?20:10)+(p.follow_up_status==='ESCALATED'?20:p.follow_up_status==='OVERDUE'?15:p.follow_up_status==='NO_RESPONSE'?10:0)}
function initials(n=''){return n.split(' ').map(x=>x[0]).slice(0,2).join('')}
function pretty(s=''){return s.replaceAll('_',' ').toLowerCase().replace(/\b\w/g,c=>c.toUpperCase())}
function when(d){if(!d)return 'Not scheduled';const diff=(new Date(d)-new Date())/3600000;if(diff<0)return `${Math.max(1,Math.round(-diff))}h overdue`;if(diff<24)return `in ${Math.max(1,Math.round(diff))}h`;return new Date(d).toLocaleDateString()}
function timeAgo(d){const m=Math.floor((Date.now()-new Date(d))/60000);if(m<1)return 'just now';if(m<60)return `${m}m ago`;if(m<1440)return `${Math.floor(m/60)}h ago`;return `${Math.floor(m/1440)}d ago`}

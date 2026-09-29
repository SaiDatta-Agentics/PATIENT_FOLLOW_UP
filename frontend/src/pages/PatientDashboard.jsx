import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../hooks/useAuth';
import useLiveUpdates from '../hooks/useLiveUpdates';
import { Activity, CalendarDays, MessageCircle, Send, ShieldCheck, Clock3, LogOut, HeartPulse, Sparkles, AlertTriangle, CheckCircle2, ChevronRight, Radio, Loader2, Bot, UserRound, XCircle } from 'lucide-react';

export default function PatientDashboard(){
  const {user,logout}=useAuth(); const nav=useNavigate(); const [data,setData]=useState(null); const [tab,setTab]=useState('care'); const [msg,setMsg]=useState(''); const [sending,setSending]=useState(false); const [slots,setSlots]=useState([]); const [notice,setNotice]=useState(''); const bottom=useRef(null);
  const load=useCallback(async()=>{const {data}=await api.get('/patients/me/summary');setData(data)},[]);
  const connected=useLiveUpdates((event)=>{if(!event.patient_id || event.patient_id===user.patientId)load()});
  useEffect(()=>{load();const id=setInterval(load,8000);return()=>clearInterval(id)},[load]);
  useEffect(()=>{if(tab==='chat') setTimeout(()=>bottom.current?.scrollIntoView({behavior:'smooth'}),50)},[data?.conversations?.length,tab]);

  const conversations=useMemo(()=>data?[...data.conversations].reverse():[],[data]);
  const upcoming=useMemo(()=>data?.appointments?.filter(a=>a.status!=='CANCELLED'&&new Date(a.date)>new Date()).sort((a,b)=>new Date(a.date)-new Date(b.date))||[],[data]);

  const send=async(text=msg)=>{const clean=text.trim();if(!clean||!data)return;setSending(true);setNotice('');try{const {data:r}=await api.post('/agent/message',{patient_id:data.patient.id,message:clean,channel:'WEB'});setMsg('');setSlots(r.slots||[]);await load();setTab('chat')}catch(e){console.error('Chat send failed',e);const d=e.response?.data?.detail;setNotice(d||e.message||'Message could not be sent. Check that the backend is running on port 8001.')}finally{setSending(false)}};
  const book=async(slot)=>{try{await api.post('/appointments',{patient_id:data.patient.id,date:new Date(slot.replace(' ','T')).toISOString(),treatment_type:data.patient.treatment});setSlots([]);setNotice('Appointment confirmed. Your clinic schedule has been updated.');await load()}catch(e){setNotice(e.response?.data?.detail||'Could not book this appointment.')}};
  const cancel=async(id)=>{await api.put(`/appointments/${id}/cancel`);setNotice('Appointment cancelled. Clinic staff can help you reschedule.');await load()};

  if(!data)return <div className="patient-loading"><Loader2 className="spin"/><span>Loading your care workspace…</span></div>;
  const p=data.patient;
  return <div className="patient-shell">
    <header className="patient-topbar">
      <div className="brand-lockup patient-brand"><div className="brand-mark small"><Activity/></div><div><span>SaiDatta Agentics</span><strong>My Care</strong></div></div>
      <div className="patient-top-actions"><span className={`live-pill ${connected?'on':''}`}><Radio/> {connected?'Live':'Reconnecting'}</span><div className="patient-identity"><div className="avatar">{p.name.split(' ').map(x=>x[0]).slice(0,2).join('')}</div><span><b>{p.name}</b><small>Patient workspace</small></span></div><button className="icon-button" onClick={()=>{logout();nav('/login')}}><LogOut/></button></div>
    </header>

    <div className="patient-content">
      <section className="patient-welcome"><div><span className="eyebrow"><Sparkles size={14}/> PERSONAL CARE ASSISTANT</span><h1>Good to see you, {p.name.split(' ')[0]}.</h1><p>Everything about your follow-up care is kept here — treatment progress, messages and appointments.</p></div><div className="care-score"><span>Care status</span><b>{pretty(p.follow_up_status)}</b><small>{p.follow_up_status==='ESCALATED'?'Clinic team has been alerted':'Your follow-up is being tracked automatically'}</small></div></section>

      <nav className="patient-tabs">{[['care','My care',HeartPulse],['chat','Care chat',MessageCircle],['appointments','Appointments',CalendarDays]].map(([key,label,Icon])=><button key={key} className={tab===key?'active':''} onClick={()=>setTab(key)}><Icon/>{label}{key==='chat'&&<span>{conversations.length}</span>}</button>)}</nav>

      {notice&&<div className="inline-notice"><CheckCircle2/>{notice}<button onClick={()=>setNotice('')}>×</button></div>}

      {tab==='care'&&<div className="patient-grid">
        <section className="care-main-card">
          <div className="card-label"><ShieldCheck/> YOUR CURRENT TREATMENT</div><h2>{p.treatment}</h2><p className="treatment-state">{p.treatment_status}</p>
          <div className="care-timeline"><Timeline active label="Visit completed" detail={p.last_visit?new Date(p.last_visit).toLocaleDateString():'Recorded by clinic'}/><Timeline active label="Follow-up active" detail={p.follow_up_date?`Scheduled ${new Date(p.follow_up_date).toLocaleString()}`:'Clinic will schedule your follow-up'}/><Timeline active={p.follow_up_status==='BOOKED'||p.follow_up_status==='COMPLETED'} label="Next visit" detail={upcoming[0]?new Date(upcoming[0].date).toLocaleString():'Not booked yet'}/></div>
          <div className="clinical-note"><AlertTriangle/><div><b>Why completion matters</b><p>Pain relief can happen before treatment is fully complete. Your dentist's recommended follow-up helps reduce the chance of reinfection or other complications. The assistant never invents fees or diagnoses — those concerns are routed to clinic staff.</p></div></div>
        </section>
        <aside className="patient-side-stack">
          <button className="action-card chat-action" onClick={()=>setTab('chat')}><div><span>Need help?</span><b>Ask your care assistant</b><small>Treatment, appointments, symptoms or fees</small></div><MessageCircle/></button>
          <div className="mini-card"><div className="mini-icon"><Clock3/></div><div><span>Automated follow-up</span><b>{data.followup_tasks[0]?.status||'Monitoring'}</b><small>{data.followup_tasks[0]?.scheduled_at?new Date(data.followup_tasks[0].scheduled_at).toLocaleString():'No task scheduled'}</small></div></div>
          <div className="mini-card"><div className="mini-icon"><CalendarDays/></div><div><span>Next appointment</span><b>{upcoming[0]?new Date(upcoming[0].date).toLocaleDateString():'Not booked'}</b><small>{upcoming[0]?new Date(upcoming[0].date).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}):'Use chat to find a time'}</small></div></div>
        </aside>
      </div>}

      {tab==='chat'&&<section className="chat-workspace">
        <div className="chat-header"><div><span className="bot-avatar"><Bot/></span><div><b>CareFlow Assistant</b><small><i className={connected?'online':''}></i>{connected?'Online · replies immediately':'Connecting…'}</small></div></div><span className="safe-badge"><ShieldCheck/> Clinic-safe responses</span></div>
        <div className="quick-prompts">{['Do I still need treatment?','Help me book an appointment','I have pain or swelling','How much will it cost?'].map(q=><button key={q} onClick={()=>send(q)}>{q}<ChevronRight/></button>)}</div>
        <div className="chat-stream">{conversations.length===0&&<div className="empty-chat"><MessageCircle/><h3>Start a conversation</h3><p>Ask about your treatment, appointment, symptoms or payment questions.</p></div>}{conversations.map(c=><Bubble key={c.id} item={c}/>)}<div ref={bottom}/></div>
        {slots.length>0&&<div className="slot-strip"><div><b>Available tomorrow</b><small>Select a time to confirm instantly</small></div><div>{slots.map(s=><button key={s} onClick={()=>book(s)}>{new Date(s.replace(' ','T')).toLocaleTimeString([], {hour:'numeric',minute:'2-digit'})}</button>)}</div></div>}
        <div className="chat-compose"><input value={msg} onChange={e=>setMsg(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}} placeholder="Type your message…"/><button onClick={()=>send()} disabled={sending||!msg.trim()}>{sending?<Loader2 className="spin"/>:<Send/>}</button></div>
      </section>}

      {tab==='appointments'&&<section className="appointment-workspace"><div className="section-heading"><div><span className="eyebrow">YOUR SCHEDULE</span><h2>Appointments</h2></div><button className="secondary-cta" onClick={()=>{setTab('chat');setMsg('Help me book an appointment')}}><MessageCircle/> Find a new time</button></div><div className="appointment-list">{data.appointments.length===0?<div className="empty-state"><CalendarDays/><h3>No appointments yet</h3><p>Ask the assistant to check available times.</p></div>:data.appointments.map(a=><div className={`appointment-row ${a.status==='CANCELLED'?'cancelled':''}`} key={a.id}><div className="date-tile"><b>{new Date(a.date).getDate()}</b><span>{new Date(a.date).toLocaleString([], {month:'short'})}</span></div><div className="appt-meta"><b>{a.treatment_type||p.treatment}</b><span>{new Date(a.date).toLocaleString([], {weekday:'long',hour:'numeric',minute:'2-digit'})}</span><small>{a.status}</small></div>{a.status!=='CANCELLED'&&<button className="text-danger" onClick={()=>cancel(a.id)}><XCircle/>Cancel</button>}</div>)}</div></section>}
    </div>
  </div>
}

function Bubble({item}){const mine=item.direction==='INBOUND';return <div className={`message-row ${mine?'mine':'agent'}`}><div className="message-avatar">{mine?<UserRound/>:<Bot/>}</div><div><div className="message-bubble">{item.message}</div><div className="message-meta">{item.intent&&item.intent.replaceAll('_',' ').toLowerCase()} · {new Date(item.created_at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</div></div></div>}
function Timeline({active,label,detail}){return <div className={`timeline-step ${active?'active':''}`}><span></span><div><b>{label}</b><small>{detail}</small></div></div>}
function pretty(s=''){return s.replaceAll('_',' ').toLowerCase().replace(/\b\w/g,c=>c.toUpperCase())}

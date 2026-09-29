import { Routes, Route, Navigate, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import useLiveUpdates from './hooks/useLiveUpdates';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import PatientDashboard from './pages/PatientDashboard';
import Patients from './pages/Patients';
import PatientDetail from './pages/PatientDetail';
import Escalations from './pages/Escalations';
import Appointments from './pages/Appointments';
import { LayoutDashboard, Users, AlertTriangle, CalendarDays, LogOut, Activity, Menu, HeartPulse, Radio, X } from 'lucide-react';
import { useState } from 'react';

const CLINIC_NAV = [
  { to:'/dashboard', label:'Live operations', icon:LayoutDashboard },
  { to:'/patients', label:'Patients', icon:Users },
  { to:'/escalations', label:'Escalations', icon:AlertTriangle },
  { to:'/appointments', label:'Schedule', icon:CalendarDays },
];

function Sidebar({ open, onClose, connected }) {
  const { user, logout } = useAuth(); const nav = useNavigate();
  return <>
    {open && <button className="sidebar-scrim" onClick={onClose}></button>}
    <aside className={`app-sidebar ${open?'open':''}`}>
      <div className="sidebar-brand"><div className="brand-mark small"><Activity/></div><div><span>SaiDatta Agentics</span><b>CareFlow AI</b></div><button className="sidebar-close" onClick={onClose}><X/></button></div>
      <div className={`live-chip ${connected?'connected':''}`}><Radio/><span>{connected?'Live updates connected':'Reconnecting live feed'}</span></div>
      <nav>
        {CLINIC_NAV.map(({to,label,icon:Icon})=><NavLink key={to} to={to} onClick={onClose} className={({isActive})=>isActive?'active':''}><Icon/><span>{label}</span></NavLink>)}
      </nav>
      <div className="sidebar-user"><div className="avatar">{user?.fullName?.split(' ').map(x=>x[0]).slice(0,2).join('')}</div><div className="user-meta"><b>{user?.fullName}</b><span>{user?.role === 'DOCTOR' ? 'Doctor workspace' : 'Staff workspace'}</span></div><button onClick={()=>{logout();nav('/login')}}><LogOut/></button></div>
    </aside>
  </>;
}

function ClinicLayout({ children }) {
  const [open,setOpen]=useState(false); const [eventTick,setEventTick]=useState(0);
  const connected = useLiveUpdates(()=>setEventTick(x=>x+1));
  return <div className="app-shell" data-event-tick={eventTick}>
    <Sidebar open={open} onClose={()=>setOpen(false)} connected={connected}/>
    <div className="app-main">
      <header className="mobile-header"><button onClick={()=>setOpen(true)}><Menu/></button><div><b>CareFlow AI</b><span>Clinic Operations</span></div><span className={`header-dot ${connected?'on':''}`}></span></header>
      <main>{children}</main>
    </div>
  </div>;
}

export default function App() {
  const { user } = useAuth();
  if (!user) return <Routes><Route path="/login" element={<Login/>}/><Route path="*" element={<Navigate to="/login" replace/>}/></Routes>;
  if (user.role === 'PATIENT') return <Routes><Route path="/dashboard" element={<PatientDashboard/>}/><Route path="*" element={<Navigate to="/dashboard" replace/>}/></Routes>;
  return <ClinicLayout><Routes>
    <Route path="/dashboard" element={<Dashboard/>}/>
    <Route path="/patients" element={<Patients/>}/>
    <Route path="/patients/:id" element={<PatientDetail/>}/>
    <Route path="/escalations" element={<Escalations/>}/>
    <Route path="/appointments" element={<Appointments/>}/>
    <Route path="*" element={<Navigate to="/dashboard" replace/>}/>
  </Routes></ClinicLayout>;
}

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Activity, Eye, EyeOff, HeartPulse, Stethoscope, UsersRound, ArrowRight, Sparkles, ShieldCheck } from 'lucide-react';

const blankRegister = { account_type: 'PATIENT', username: '', password: '', full_name: '', email: '', phone: '', clinic_access_code: '' };

export default function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState('signin');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [reg, setReg] = useState(blankRegister);
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const fail = (err) => {
    if (err.response?.data?.detail) return setError(String(err.response.data.detail));
    if (err.code === 'ERR_NETWORK') return setError('Cannot connect to the agent backend. Start FastAPI on port 8001.');
    setError('Something went wrong. Check the backend terminal and try again.');
  };

  const signIn = async (e) => {
    e.preventDefault(); setError(''); setLoading(true);
    try { await login(username.trim(), password); navigate('/dashboard', { replace: true }); }
    catch (err) { fail(err); }
    finally { setLoading(false); }
  };

  const create = async (e) => {
    e.preventDefault(); setError(''); setLoading(true);
    try {
      await register({ ...reg, username: reg.username.trim(), email: reg.email.trim() || null, phone: reg.phone.trim() || null });
      navigate('/dashboard', { replace: true });
    } catch (err) { fail(err); }
    finally { setLoading(false); }
  };

  const pickDemo = (u, p) => { setMode('signin'); setUsername(u); setPassword(p); setError(''); };

  return (
    <div className="auth-shell">
      <section className="auth-hero">
        <div className="brand-lockup"><div className="brand-mark"><Activity /></div><div><span>SaiDatta Agentics</span><strong>CareFlow AI</strong></div></div>
        <div className="auth-copy">
          <span className="eyebrow"><Sparkles size={14}/> REAL-TIME PATIENT FOLLOW-UP</span>
          <h1>Care that continues<br/>after the visit.</h1>
          <p>Automated follow-ups, patient conversations, appointment recovery and staff escalation — in one live care workspace.</p>
          <div className="hero-points">
            <div><HeartPulse/><span><b>Clinical context</b><small>Respond with treatment-aware guidance</small></span></div>
            <div><ShieldCheck/><span><b>Safe escalation</b><small>Symptoms and fees go to clinic staff</small></span></div>
            <div><Activity/><span><b>Live automation</b><small>New data enters the same follow-up engine</small></span></div>
          </div>
        </div>
        <div className="auth-orbit"><div className="pulse-dot"></div><span>Automation worker active</span></div>
      </section>

      <main className="auth-panel">
        <div className="auth-card">
          <div className="auth-tabs">
            <button className={mode==='signin'?'active':''} onClick={()=>{setMode('signin');setError('')}}>Sign in</button>
            <button className={mode==='signup'?'active':''} onClick={()=>{setMode('signup');setError('')}}>Create account</button>
          </div>

          {mode === 'signin' ? (
            <>
              <div className="auth-heading"><h2>Welcome back</h2><p>Enter your patient or clinic workspace.</p></div>
              <form onSubmit={signIn} className="auth-form">
                <Field label="Username"><input value={username} onChange={e=>setUsername(e.target.value)} placeholder="e.g. john" autoComplete="username" required /></Field>
                <Field label="Password"><div className="password-field"><input type={showPw?'text':'password'} value={password} onChange={e=>setPassword(e.target.value)} placeholder="Your password" autoComplete="current-password" required/><button type="button" onClick={()=>setShowPw(!showPw)}>{showPw?<EyeOff/>:<Eye/>}</button></div></Field>
                {error && <div className="form-error">{error}</div>}
                <button className="primary-cta" disabled={loading}>{loading?'Signing in…':<>Enter workspace <ArrowRight size={17}/></>}</button>
              </form>
              <div className="demo-login">
                <div className="demo-title"><span>Try the live demo</span><small>Click to fill credentials</small></div>
                <div className="demo-grid">
                  <button onClick={()=>pickDemo('john','patient123')}><HeartPulse/><span><b>Patient</b><small>john / patient123</small></span></button>
                  <button onClick={()=>pickDemo('drjones','doctor123')}><Stethoscope/><span><b>Doctor</b><small>drjones / doctor123</small></span></button>
                  <button onClick={()=>pickDemo('staff1','staff123')}><UsersRound/><span><b>Staff</b><small>staff1 / staff123</small></span></button>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="auth-heading"><h2>Create your account</h2><p>Patient accounts link to one care profile. Doctor and staff accounts enter the clinic workspace.</p></div>
              <form onSubmit={create} className="auth-form">
                <div className="role-picker">
                  {[['PATIENT','Patient',HeartPulse],['DOCTOR','Doctor',Stethoscope],['STAFF','Staff',UsersRound]].map(([value,label,Icon])=><button type="button" key={value} className={reg.account_type===value?'active':''} onClick={()=>setReg({...reg,account_type:value})}><Icon/><span>{label}</span></button>)}
                </div>
                <div className="form-two"><Field label="Full name"><input value={reg.full_name} onChange={e=>setReg({...reg,full_name:e.target.value})} required/></Field><Field label="Username"><input value={reg.username} onChange={e=>setReg({...reg,username:e.target.value})} required/></Field></div>
                <div className="form-two"><Field label="Email"><input type="email" value={reg.email} onChange={e=>setReg({...reg,email:e.target.value})}/></Field><Field label="Phone"><input value={reg.phone} onChange={e=>setReg({...reg,phone:e.target.value})}/></Field></div>
                <Field label="Password"><input type="password" minLength={6} maxLength={72} value={reg.password} onChange={e=>setReg({...reg,password:e.target.value})} placeholder="At least 6 characters" required/></Field>
                {reg.account_type !== 'PATIENT' && <Field label="Clinic access code"><input value={reg.clinic_access_code} onChange={e=>setReg({...reg,clinic_access_code:e.target.value})} placeholder="Demo: CLINIC-DEMO" required/></Field>}
                {error && <div className="form-error">{error}</div>}
                <button className="primary-cta" disabled={loading}>{loading?'Creating account…':<>Create & enter workspace <ArrowRight size={17}/></>}</button>
              </form>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

function Field({label,children}){return <label className="field"><span>{label}</span>{children}</label>}

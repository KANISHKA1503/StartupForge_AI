import React, { useState, useEffect, useRef } from 'react';

// Helpers to parse markdown-wrapped JSON safely
const parseAgentJson = (raw) => {
  if (!raw) return null;
  if (typeof raw === 'object') return raw;
  try {
    return JSON.parse(raw);
  } catch (e) {
    const match = raw.match(/```json\s*([\s\S]*?)\s*```/);
    if (match) {
      try {
        return JSON.parse(match[1]);
      } catch (e2) {
        console.error("Failed parsing extracted json", e2);
      }
    }
    try {
      const clean = raw.replace(/```json|```/g, '').trim();
      return JSON.parse(clean);
    } catch (e3) {
      console.error("Failed clean parsing", e3);
    }
  }
  return null;
};

function App() {
  // Navigation & Config State
  const [activeTab, setActiveTab] = useState('home'); // 'home', 'dashboard' or 'settings'
  const [config, setConfig] = useState({ groq_api_key_set: false, demo_mode: true });
  const [inputKey, setInputKey] = useState('');
  const [demoModeToggle, setDemoModeToggle] = useState(true);

  // Profile Inputs
  const [profile, setProfile] = useState({
    skills: 'Python, React',
    interests: 'AI Education',
    experience: 'Student',
    budget: 'Low',
    goal: 'Build SaaS Startup'
  });

  // Pipeline Status
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0); // 0 = idle, 1 = discovery, 2 = market, 3 = planner, 4 = pitch, 5 = done
  const [stepStatus, setStepStatus] = useState({
    1: 'Idle',
    2: 'Idle',
    3: 'Idle',
    4: 'Idle'
  });
  const [logs, setLogs] = useState('System ready. Booting accelerator...\n');
  const [activeOutputTab, setActiveOutputTab] = useState('tab-blueprint');
  const [unlockedTabs, setUnlockedTabs] = useState({
    'tab-blueprint': false,
    'tab-market': false,
    'tab-mvp': false,
    'tab-pitch': false
  });

  // Agent Output Results
  const [discoveryResult, setDiscoveryResult] = useState(null);
  const [blueprint, setBlueprint] = useState(null);
  const [marketResult, setMarketResult] = useState(null);
  const [mvpResult, setMvpResult] = useState(null);
  const [pitchResult, setPitchResult] = useState(null);

  // Pitch Deck Slide Navigation
  const [activeSlide, setActiveSlide] = useState(0);

  const logsEndRef = useRef(null);

  // Scroll logs terminal automatically
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Load backend configuration status at startup
  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/config');
      const data = await res.json();
      setConfig(data);
      setDemoModeToggle(data.demo_mode);
    } catch (e) {
      console.error("Error fetching config from backend:", e);
      setLogs((prev) => prev + "WARNING: Could not connect to API server at http://localhost:8000. Is it running?\n");
    }
  };

  const saveSettings = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ groq_api_key: inputKey, demo_mode: demoModeToggle })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setLogs((prev) => prev + `SETTINGS SAVED: Demo Mode is now ${demoModeToggle ? 'ON' : 'OFF'}\n`);
        fetchConfig();
        setActiveTab('dashboard');
      }
    } catch (e) {
      alert("Error saving settings");
    }
  };

  // Pipeline Execution Logic
  const runPipeline = async (e) => {
    if (e) e.preventDefault();
    if (isRunning) return;

    setIsRunning(true);
    setLogs("Accelerator pipeline started...\n");
    setCurrentStep(1);
    setStepStatus((prev) => ({ ...prev, 1: 'Running...', 2: 'Idle', 3: 'Idle', 4: 'Idle' }));
    
    // Clear outputs
    setDiscoveryResult(null);
    setBlueprint(null);
    setMarketResult(null);
    setMvpResult(null);
    setPitchResult(null);
    setUnlockedTabs({
      'tab-blueprint': false,
      'tab-market': false,
      'tab-mvp': false,
      'tab-pitch': false
    });

    try {
      // Step 1: Concept Discovery
      setLogs((prev) => prev + ">>>> TRIGGERING CONCEPT DISCOVERY AGENT <<<<\n");
      const discRes = await fetch('http://localhost:8000/api/agents/discovery', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile)
      });
      const discData = await discRes.json();
      
      if (discData.status !== 'success') {
        throw new Error(discData.detail || "Discovery Agent failed");
      }

      setLogs((prev) => prev + (discData.logs || "") + "Concept Discovery completed successfully.\n");
      setDiscoveryResult(discData.result);
      
      const bp = parseAgentJson(discData.result.blueprint);
      setBlueprint(bp);
      
      setStepStatus((prev) => ({ ...prev, 1: 'Completed' }));
      setUnlockedTabs((prev) => ({ ...prev, 'tab-blueprint': true }));
      setActiveOutputTab('tab-blueprint');

      // Scroll to outputs
      setTimeout(() => {
        document.getElementById('output-section')?.scrollIntoView({ behavior: 'smooth' });
      }, 500);

      // Step 2: Market Validation
      setCurrentStep(2);
      setStepStatus((prev) => ({ ...prev, 2: 'Running...' }));
      setLogs((prev) => prev + "\n>>>> TRIGGERING MARKET VALIDATION AGENT <<<<\n");

      // Build research payload based on blueprint
      const researchPayload = {
        startup_name: bp?.startup_name || "SaaS Venture",
        problem: bp?.problem_statement || profile.interests,
        solution: bp?.solution || "AI Solution",
        target_users: bp?.target_users || "General Public"
      };

      const resRes = await fetch('http://localhost:8000/api/agents/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(researchPayload)
      });
      const resData = await resRes.json();

      if (resData.status !== 'success') {
        throw new Error(resData.detail || "Market Validation Agent failed");
      }

      setLogs((prev) => prev + (resData.logs || "") + "Market Validation completed successfully.\n");
      setMarketResult(resData.result);
      setStepStatus((prev) => ({ ...prev, 2: 'Completed' }));
      setUnlockedTabs((prev) => ({ ...prev, 'tab-market': true }));

      // Step 3: MVP Technical Architect
      setCurrentStep(3);
      setStepStatus((prev) => ({ ...prev, 3: 'Running...' }));
      setLogs((prev) => prev + "\n>>>> TRIGGERING MVP TECHNICAL ARCHITECT AGENT <<<<\n");

      const plannerPayload = {
        startup_idea: researchPayload,
        user_profile: profile
      };

      const planRes = await fetch('http://localhost:8000/api/agents/mvp-planner', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(plannerPayload)
      });
      const planData = await planRes.json();

      if (planData.status !== 'success') {
        throw new Error(planData.detail || "MVP Planner Agent failed");
      }

      setLogs((prev) => prev + (planData.logs || "") + "MVP Technical Architecture design completed successfully.\n");
      setMvpResult(planData.result);
      setStepStatus((prev) => ({ ...prev, 3: 'Completed' }));
      setUnlockedTabs((prev) => ({ ...prev, 'tab-mvp': true }));

      // Step 4: Investor Pitch Deck
      setCurrentStep(4);
      setStepStatus((prev) => ({ ...prev, 4: 'Running...' }));
      setLogs((prev) => prev + "\n>>>> TRIGGERING INVESTOR PITCH DECK AGENT <<<<\n");

      // Extract architect parameters
      const parsedFeatures = parseAgentJson(planData.result.features);
      const parsedRevenue = planData.result.revenue_strategy;
      const parsedSuccess = parseAgentJson(planData.result.success_probability);

      const pitchPayload = {
        startup_context: researchPayload,
        market_validation: resData.result.validation || "Validated Market",
        architect_report: {
          features: parsedFeatures?.mvp_features?.map(f => f.name).join(", ") || "MVP features",
          revenue_strategy: parsedRevenue || "SaaS",
          success_probability: parsedSuccess?.success_probability || "80"
        }
      };

      const pitchRes = await fetch('http://localhost:8000/api/agents/pitch-deck', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(pitchPayload)
      });
      const pitchData = await pitchRes.json();

      if (pitchData.status !== 'success') {
        throw new Error(pitchData.detail || "Pitch Deck Agent failed");
      }

      setLogs((prev) => prev + (pitchData.logs || "") + "Investor Pitch Deck generation completed successfully.\n\n=== PIPELINE FINISHED SUCCESSFUL ===\n");
      
      const parsedSlides = parseAgentJson(pitchData.result);
      setPitchResult(parsedSlides || []);
      setActiveSlide(0);

      setStepStatus((prev) => ({ ...prev, 4: 'Completed' }));
      setUnlockedTabs((prev) => ({ ...prev, 'tab-pitch': true }));
      setCurrentStep(5);

    } catch (error) {
      setLogs((prev) => prev + `\nFATAL ERROR: ${error.message}\nPipeline stopped.\n`);
      setStepStatus((prev) => ({ ...prev, [currentStep]: 'Failed' }));
    } finally {
      setIsRunning(false);
    }
  };

  // Parsing individual JSON structures safely for display
  const competitorsData = parseAgentJson(marketResult?.competitors);
  const painPointsData = parseAgentJson(marketResult?.pain_points);
  const segmentsData = parseAgentJson(marketResult?.validation);
  const partnerMemo = parseAgentJson(marketResult?.investor_feedback);

  const mvpFeatures = parseAgentJson(mvpResult?.features);
  const mvpTech = parseAgentJson(mvpResult?.tech_stack);
  const mvpApis = parseAgentJson(mvpResult?.apis);
  const mvpUi = parseAgentJson(mvpResult?.ui);
  const mvpRoadmap = parseAgentJson(mvpResult?.roadmap);
  const mvpCosts = parseAgentJson(mvpResult?.costs);
  const mvpSuccess = parseAgentJson(mvpResult?.success_probability);

  return (
    <div class="app-container">
      {/* Top Navbar */}
      <header class="top-nav-bar">
        <div class="brand">
          <i class="fa-solid fa-fire-burner brand-icon"></i>
          <span class="brand-name">StartupForge<span class="brand-highlight">AI</span></span>
        </div>
        <nav class="top-nav-menu">
          <a 
            href="#" 
            className={`top-nav-item ${activeTab === 'home' ? 'active' : ''}`}
            onClick={(e) => { e.preventDefault(); setActiveTab('home'); }}
          >
            <i class="fa-solid fa-house"></i>
            <span>Home</span>
          </a>
          <a 
            href="#" 
            className={`top-nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={(e) => { e.preventDefault(); setActiveTab('dashboard'); }}
          >
            <i class="fa-solid fa-rocket"></i>
            <span>Accelerator</span>
          </a>
          <a 
            href="#" 
            className={`top-nav-item ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={(e) => { e.preventDefault(); setActiveTab('settings'); }}
          >
            <i class="fa-solid fa-sliders"></i>
            <span>Settings</span>
          </a>
        </nav>
        <div class="top-nav-right">
          <div class="status-indicator">
            <span className={`status-dot pulse ${config.demo_mode ? 'demo' : 'active'}`}></span>
            <span class="status-text">{config.demo_mode ? 'Demo Mode' : 'Live Mode'}</span>
          </div>
          <div 
            className={`settings-pill ${config.groq_api_key_set ? 'key-active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <i class="fa-solid fa-key"></i>
            <span>{config.groq_api_key_set ? 'Groq Key Active' : 'Configure API Key'}</span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main class="main-content">

        {/* TAB CONTENTS */}
        {activeTab === 'home' && (
          <div class="tab-pane active">
            <div class="hero-section">
              <div class="hero-content">
                <span class="hero-badge"><i class="fa-solid fa-wand-magic-sparkles"></i> Autonomous Incubator</span>
                <h2 class="hero-title">Forge Your Startup Idea with Multi-Agent Intelligence</h2>
                <p class="hero-desc">
                  StartupForge AI accelerates your entrepreneurial journey. Our specialized AI agents analyze your profile, validate market demand, engineer your technical architecture, and structure your investor pitch deck instantly.
                </p>
                <button class="btn btn-primary hero-cta" onClick={() => setActiveTab('dashboard')}>
                  <i class="fa-solid fa-rocket"></i> Launch Accelerator Hub
                </button>
              </div>
            </div>

            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-val">14,250+</div>
                <div class="stat-lbl">Startups Evaluated</div>
              </div>
              <div class="stat-card">
                <div class="stat-val">5,400+</div>
                <div class="stat-lbl">YC Startups Indexed</div>
              </div>
              <div class="stat-card">
                <div class="stat-val">4 Active</div>
                <div class="stat-lbl">Specialized Agents</div>
              </div>
              <div class="stat-card">
                <div class="stat-val">&lt; 1 Minute</div>
                <div class="stat-lbl">Average Build Time</div>
              </div>
            </div>

            <div class="section-header-center">
              <h2>How StartupForge AI Works</h2>
              <p>Four specialized, collaborative AI agents guide you from spark to structure.</p>
            </div>

            <div class="features-grid">
              <div class="feature-card">
                <div class="icon-wrapper indigo">
                  <i class="fa-solid fa-magnifying-glass-chart"></i>
                </div>
                <div class="feature-details">
                  <h3>1. Concept Discovery Agent</h3>
                  <p>
                    Analyzes your skills, interests, and budget constraints. Retrieves historical YC trends to formulate a customized startup blueprint.
                  </p>
                </div>
              </div>

              <div class="feature-card">
                <div class="icon-wrapper emerald">
                  <i class="fa-solid fa-scale-balanced"></i>
                </div>
                <div class="feature-details">
                  <h3>2. Market Validation Agent</h3>
                  <p>
                    Scours HackerNews threads and StackOverflow questions to find developer pain points, identifies direct competitors, and runs a mock YC partner verdict.
                  </p>
                </div>
              </div>

              <div class="feature-card">
                <div class="icon-wrapper cyan">
                  <i class="fa-solid fa-sitemap"></i>
                </div>
                <div class="feature-details">
                  <h3>3. MVP Planner & Architect</h3>
                  <p>
                    Designs your database schemas, creates REST API lists, outlines a 4-week development roadmap, and estimates hosting/API runtime cost tiers.
                  </p>
                </div>
              </div>

              <div class="feature-card">
                <div class="icon-wrapper violet">
                  <i class="fa-solid fa-chalkboard-user"></i>
                </div>
                <div class="feature-details">
                  <h3>4. Pitch Deck Synthesizer</h3>
                  <p>
                    Consolidates details from the discovery, research, and architect phases into a concise, 10-slide slide presentation ready for investors.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'dashboard' ? (
          <div class="tab-pane active">
            <div class="grid-container">
              {/* Profile Inputs */}
              <div class="card form-card">
                <div class="card-header">
                  <i class="fa-solid fa-id-card-clip card-icon"></i>
                  <h2>Founder Profile</h2>
                </div>
                <p class="card-description">Describe your constraints and goals. Our agents will align all recommendations to your profile.</p>
                
                <form onSubmit={runPipeline}>
                  <div class="form-group">
                    <label htmlFor="skills"><i class="fa-solid fa-code"></i> Technical Skills</label>
                    <input 
                      type="text" 
                      id="skills" 
                      value={profile.skills} 
                      onChange={(e) => setProfile({ ...profile, skills: e.target.value })}
                      placeholder="e.g., Python, React, UI Design" 
                      required 
                      disabled={isRunning}
                    />
                  </div>

                  <div class="form-group">
                    <label htmlFor="interests"><i class="fa-solid fa-lightbulb"></i> Domain Interests</label>
                    <input 
                      type="text" 
                      id="interests" 
                      value={profile.interests} 
                      onChange={(e) => setProfile({ ...profile, interests: e.target.value })}
                      placeholder="e.g., AI Education, FinTech" 
                      required 
                      disabled={isRunning}
                    />
                  </div>

                  <div class="form-group">
                    <label htmlFor="experience"><i class="fa-solid fa-graduation-cap"></i> Experience Level</label>
                    <input 
                      type="text" 
                      id="experience" 
                      value={profile.experience} 
                      onChange={(e) => setProfile({ ...profile, experience: e.target.value })}
                      placeholder="e.g., Student, Tech Lead" 
                      required 
                      disabled={isRunning}
                    />
                  </div>

                  <div class="form-group">
                    <label htmlFor="budget"><i class="fa-solid fa-wallet"></i> Budget Tier</label>
                    <select 
                      id="budget" 
                      value={profile.budget} 
                      onChange={(e) => setProfile({ ...profile, budget: e.target.value })}
                      disabled={isRunning}
                    >
                      <option value="Low">Low (Under $500)</option>
                      <option value="Medium">Medium ($500 - $5,000)</option>
                      <option value="High">High ($5,000+)</option>
                    </select>
                  </div>

                  <div class="form-group">
                    <label htmlFor="goal"><i class="fa-solid fa-bullseye"></i> Startup Goal</label>
                    <input 
                      type="text" 
                      id="goal" 
                      value={profile.goal} 
                      onChange={(e) => setProfile({ ...profile, goal: e.target.value })}
                      placeholder="e.g., Build SaaS Startup" 
                      required 
                      disabled={isRunning}
                    />
                  </div>

                  <button type="submit" class="btn btn-primary" disabled={isRunning}>
                    <i className={isRunning ? "fa-solid fa-circle-notch fa-spin" : "fa-solid fa-play"}></i>
                    {isRunning ? "Running Agents..." : "Run Accelerator Pipeline"}
                  </button>
                </form>
              </div>

              {/* Pipeline Stepper & Logs */}
              <div class="column-right-flex">
                <div class="card stepper-card">
                  <div class="card-header">
                    <i class="fa-solid fa-network-wired card-icon"></i>
                    <h2>Pipeline Tracker</h2>
                  </div>
                  <div class="stepper">
                    <div className={`step ${currentStep === 1 ? 'active' : ''} ${currentStep > 1 ? 'completed' : ''}`}>
                      <div class="step-icon">
                        {currentStep > 1 ? <i class="fa-solid fa-check"></i> : <i class="fa-solid fa-magnifying-glass"></i>}
                      </div>
                      <div class="step-info">
                        <span class="step-title">1. Discovery</span>
                        <span class="step-status">{stepStatus[1]}</span>
                      </div>
                    </div>
                    <div className={`step ${currentStep === 2 ? 'active' : ''} ${currentStep > 2 ? 'completed' : ''}`}>
                      <div class="step-icon">
                        {currentStep > 2 ? <i class="fa-solid fa-check"></i> : <i class="fa-solid fa-chart-line"></i>}
                      </div>
                      <div class="step-info">
                        <span class="step-title">2. Validation</span>
                        <span class="step-status">{stepStatus[2]}</span>
                      </div>
                    </div>
                    <div className={`step ${currentStep === 3 ? 'active' : ''} ${currentStep > 3 ? 'completed' : ''}`}>
                      <div class="step-icon">
                        {currentStep > 3 ? <i class="fa-solid fa-check"></i> : <i class="fa-solid fa-cubes"></i>}
                      </div>
                      <div class="step-info">
                        <span class="step-title">3. MVP Planner</span>
                        <span class="step-status">{stepStatus[3]}</span>
                      </div>
                    </div>
                    <div className={`step ${currentStep === 4 ? 'active' : ''} ${currentStep > 4 ? 'completed' : ''}`}>
                      <div class="step-icon">
                        {currentStep > 4 ? <i class="fa-solid fa-check"></i> : <i class="fa-solid fa-images"></i>}
                      </div>
                      <div class="step-info">
                        <span class="step-title">4. Pitch Deck</span>
                        <span class="step-status">{stepStatus[4]}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Console Logs */}
                <div class="card console-card">
                  <div class="card-header console-header">
                    <div class="header-left">
                      <i class="fa-solid fa-terminal card-icon"></i>
                      <h2>Agent Execution Console</h2>
                    </div>
                    <div class="console-controls">
                      <span class="dot red"></span>
                      <span class="dot yellow"></span>
                      <span class="dot green"></span>
                    </div>
                  </div>
                  <div class="terminal-body">
                    {logs}
                    <div ref={logsEndRef} />
                  </div>
                </div>
              </div>
            </div>

            {/* Agent Outputs */}
            <div className={`card output-card ${discoveryResult ? '' : 'hidden'}`} id="output-section">
              <div class="output-navbar">
                <div 
                  className={`output-tab-btn ${activeOutputTab === 'tab-blueprint' ? 'active' : ''}`}
                  onClick={() => unlockedTabs['tab-blueprint'] && setActiveOutputTab('tab-blueprint')}
                >
                  <i class="fa-solid fa-compass"></i> 1. Concept Blueprint
                </div>
                <div 
                  className={`output-tab-btn ${unlockedTabs['tab-market'] ? '' : 'disabled'} ${activeOutputTab === 'tab-market' ? 'active' : ''}`}
                  onClick={() => unlockedTabs['tab-market'] && setActiveOutputTab('tab-market')}
                >
                  <i class="fa-solid fa-scale-balanced"></i> 2. Market Validation
                </div>
                <div 
                  className={`output-tab-btn ${unlockedTabs['tab-mvp'] ? '' : 'disabled'} ${activeOutputTab === 'tab-mvp' ? 'active' : ''}`}
                  onClick={() => unlockedTabs['tab-mvp'] && setActiveOutputTab('tab-mvp')}
                >
                  <i class="fa-solid fa-sitemap"></i> 3. Technical MVP
                </div>
                <div 
                  className={`output-tab-btn ${unlockedTabs['tab-pitch'] ? '' : 'disabled'} ${activeOutputTab === 'tab-pitch' ? 'active' : ''}`}
                  onClick={() => unlockedTabs['tab-pitch'] && setActiveOutputTab('tab-pitch')}
                >
                  <i class="fa-solid fa-chalkboard-user"></i> 4. Investor Pitch
                </div>
              </div>

              <div class="output-tabs-content">
                {/* Tab 1: Blueprint */}
                {activeOutputTab === 'tab-blueprint' && blueprint && (
                  <div class="output-pane active">
                    <div class="blueprint-layout">
                      <div class="blueprint-main">
                        <div class="header-highlight">
                          <span class="badge badge-indigo">Recommended Idea</span>
                          <h3 class="blueprint-startup-name">{blueprint.startup_name}</h3>
                        </div>
                        <div class="info-block">
                          <h4><i class="fa-solid fa-triangle-exclamation text-rose"></i> Problem Statement</h4>
                          <p>{blueprint.problem_statement}</p>
                        </div>
                        <div class="info-block">
                          <h4><i class="fa-solid fa-check-double text-teal"></i> Proposed Solution</h4>
                          <p>{blueprint.solution}</p>
                        </div>
                        <div class="info-block">
                          <h4><i class="fa-solid fa-users text-violet"></i> Target Audience</h4>
                          <p>{blueprint.target_users}</p>
                        </div>
                      </div>
                      
                      <div class="blueprint-side">
                        <div class="info-block">
                          <h4><i class="fa-solid fa-money-bill-wave text-cyan"></i> Business Model</h4>
                          <p>{blueprint.revenue_model}</p>
                        </div>
                        <div class="info-block">
                          <h4><i class="fa-solid fa-shield-halved text-cyan"></i> Competitive Advantage</h4>
                          <p>{blueprint.competitive_advantage}</p>
                        </div>
                        <div class="info-block">
                          <h4><i class="fa-solid fa-clock text-cyan"></i> Why Now?</h4>
                          <p>{blueprint.why_now}</p>
                        </div>
                        <div class="info-block">
                          <h4><i class="fa-solid fa-rocket text-cyan"></i> Go-to-Market</h4>
                          <p>{blueprint.go_to_market_strategy}</p>
                        </div>
                      </div>
                    </div>
                    {unlockedTabs['tab-market'] && (
                      <div class="action-footer">
                        <button class="btn btn-secondary next-agent-btn" onClick={() => setActiveOutputTab('tab-market')}>
                          Go to Market Validation <i class="fa-solid fa-arrow-right"></i>
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Tab 2: Market Validation */}
                {activeOutputTab === 'tab-market' && marketResult && (
                  <div class="output-pane active">
                    <div class="market-layout">
                      <div class="market-metrics">
                        <h4>Market Scorecard</h4>
                        <div class="metrics-grid">
                          <div class="metric-gauge">
                            <div class="gauge-value">{segmentsData?.market_demand_score || 0}%</div>
                            <div class="gauge-label">Market Demand</div>
                          </div>
                          <div class="metric-gauge">
                            <div class="gauge-value">{segmentsData?.founder_market_fit_score || 0}%</div>
                            <div class="gauge-label">Founder-Market Fit</div>
                          </div>
                          <div class="metric-gauge">
                            <div class="gauge-value">{segmentsData?.buildability_score || 0}%</div>
                            <div class="gauge-label">Buildability</div>
                          </div>
                          <div class="metric-gauge">
                            <div class="gauge-value">{segmentsData?.scalability_score || 0}%</div>
                            <div class="gauge-label">Scalability</div>
                          </div>
                        </div>
                      </div>

                      <div class="market-details">
                        {partnerMemo && (
                          <div class="info-block">
                            <h4><i class="fa-solid fa-hand-holding-dollar text-emerald"></i> YC Investor Agent Feedback</h4>
                            <div class="yc-memo-container">
                              <div class="memo-header">
                                <span class="badge badge-emerald">{partnerMemo.investment_recommendation || 'YES'}</span>
                                <span class="score">Fundability Score: {partnerMemo.fundability_score || 0}/100</span>
                              </div>
                              <div class="memo-content">
                                <p><strong>Founder Fit Analysis:</strong> {partnerMemo.founder_market_fit_analysis}</p>
                                <p><strong>Core Strengths:</strong></p>
                                <ul>
                                  {partnerMemo.strengths?.map((s, idx) => <li key={idx}>{s}</li>)}
                                </ul>
                                <p><strong>Identified Weaknesses:</strong></p>
                                <ul>
                                  {partnerMemo.weaknesses?.map((w, idx) => <li key={idx}>{w}</li>)}
                                </ul>
                                <p><strong>Key Risks:</strong></p>
                                <ul>
                                  {partnerMemo.risks?.map((r, idx) => <li key={idx}>{r}</li>)}
                                </ul>
                              </div>
                            </div>
                          </div>
                        )}

                        <div class="grid-2-col">
                          <div class="info-block">
                            <h4><i class="fa-solid fa-heart-crack text-rose"></i> Identified Pain Points & Complaints</h4>
                            <div class="scrolling-box">
                              {painPointsData?.common_complaints?.map((c, i) => `• ${c}\n`) || "No major complaints found."}
                              {painPointsData?.missing_features && "\nMissing Features Sought:\n" + painPointsData.missing_features.map(f => `• ${f}\n`).join("")}
                            </div>
                          </div>
                          <div class="info-block">
                            <h4><i class="fa-solid fa-users-viewfinder text-indigo"></i> Customer Segments & Feasibility</h4>
                            <div class="scrolling-box">
                              {`Beachhead Market: ${segmentsData?.beachhead_market || 'N/A'}\n`}
                              {`Early Adopters: ${segmentsData?.early_adopters || 'N/A'}\n`}
                              {`Time to MVP: ${segmentsData?.time_to_mvp || 'N/A'}\n`}
                              {`Cost to Build: ${segmentsData?.mvp_cost_estimate || 'N/A'}\n`}
                              {`Founder Fit Verdict: ${segmentsData?.can_founder_build || 'N/A'}`}
                            </div>
                          </div>
                        </div>

                        <div class="info-block">
                          <h4><i class="fa-solid fa-circle-nodes text-cyan"></i> Similar YC Competitors (Retrieved via ChromaDB)</h4>
                          <div class="yc-startups-list">
                            {marketResult.yc_startups?.map((c, i) => {
                              const nameMatch = c.match(/Startup Name:\s*(.*?)\n/);
                              const lineMatch = c.match(/One Liner:\s*(.*?)\n/);
                              return (
                                <div class="yc-competitor-card" key={i}>
                                  <h5>{nameMatch ? nameMatch[1] : `Competitor ${i+1}`}</h5>
                                  <p>{lineMatch ? lineMatch[1] : c.substring(0, 120) + "..."}</p>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    </div>
                    {unlockedTabs['tab-mvp'] && (
                      <div class="action-footer">
                        <button class="btn btn-secondary next-agent-btn" onClick={() => setActiveOutputTab('tab-mvp')}>
                          Go to Technical MVP <i class="fa-solid fa-arrow-right"></i>
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Tab 3: MVP Architect */}
                {activeOutputTab === 'tab-mvp' && mvpResult && (
                  <div class="output-pane active">
                    <div class="mvp-layout">
                      <div class="mvp-summary-bar">
                        <div class="mvp-stat">
                          <span class="stat-num">{mvpResult.buildability ? mvpResult.buildability.match(/\d+\/\d+/)?.[0] || '9/10' : '9/10'}</span>
                          <span class="stat-name">Buildability Score</span>
                        </div>
                        <div class="mvp-stat">
                          <span class="stat-num">{mvpResult.buildability ? mvpResult.buildability.match(/Time To MVP:\s*(\w+-\w+\s*\w+|\w+\s*\w+)/)?.[1] || '3 Weeks' : '3 Weeks'}</span>
                          <span class="stat-name">Build Duration</span>
                        </div>
                        <div class="mvp-stat">
                          <span class="stat-num">{mvpSuccess?.success_probability || 85}%</span>
                          <span class="stat-name">Success Chance</span>
                        </div>
                      </div>

                      <div class="grid-2-col gap-large mt-large">
                        <div>
                          <div class="info-block">
                            <h4><i class="fa-solid fa-clipboard-list text-teal"></i> Feature Scope Breakdown</h4>
                            <div id="mvp-features-list">
                              {mvpFeatures?.mvp_features?.map((f, i) => (
                                <div class="feature-item" key={i}>
                                  <h5>{f.name}</h5>
                                  <p>{f.description}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                          
                          <div class="info-block">
                            <h4><i class="fa-solid fa-layer-group text-violet"></i> Recommended Tech Stack</h4>
                            <div class="tech-stack-container">
                              {mvpTech && Object.entries(mvpTech).map(([key, val]) => (
                                <div class="tech-pill" key={key}>
                                  <span class="tech-label">{key.replace('_', ' ')}</span>
                                  <span class="tech-val">{val}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>

                        <div>
                          <div class="info-block">
                            <h4><i class="fa-solid fa-database text-amber"></i> Database Schema</h4>
                            <div class="code-container">
                              <pre><code class="language-sql">{mvpResult.database}</code></pre>
                            </div>
                          </div>

                          <div class="info-block">
                            <h4><i class="fa-solid fa-gears text-rose"></i> API Routes Checklist</h4>
                            <div class="api-list">
                              {mvpApis?.map((api, idx) => (
                                <div class="api-item" key={idx}>
                                  <span className={`api-method ${api.method.toLowerCase()}`}>{api.method}</span>
                                  <span class="api-route">{api.route}</span>
                                  <span class="api-desc">{api.description}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>

                      <div class="grid-2-col gap-large mt-large">
                        <div class="info-block">
                          <h4><i class="fa-solid fa-calendar-week text-sky"></i> 4-Week Dev Roadmap</h4>
                          <div class="timeline">
                            {mvpRoadmap?.map((day, idx) => (
                              <div class="timeline-item" key={idx}>
                                <div class="timeline-dot"></div>
                                <div class="timeline-header">{day.week}</div>
                                <div class="timeline-body">{day.goal}</div>
                              </div>
                            ))}
                          </div>
                        </div>

                        <div class="info-block">
                          <h4><i class="fa-solid fa-money-bill-transfer text-emerald"></i> Infrastructure Cost Projection</h4>
                          <table class="cost-table">
                            <thead>
                              <tr>
                                <th>Category</th>
                                <th>Estimated Cost</th>
                              </tr>
                            </thead>
                            <tbody>
                              {mvpCosts && Object.entries(mvpCosts).map(([cat, cost]) => (
                                <tr key={cat}>
                                  <td>{cat.replace('_', ' ')}</td>
                                  <td>{cost}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                    {unlockedTabs['tab-pitch'] && (
                      <div class="action-footer">
                        <button class="btn btn-secondary next-agent-btn" onClick={() => setActiveOutputTab('tab-pitch')}>
                          Go to Pitch Deck <i class="fa-solid fa-arrow-right"></i>
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Tab 4: Pitch Deck */}
                {activeOutputTab === 'tab-pitch' && pitchResult && (
                  <div class="output-pane active">
                    <div class="pitch-layout">
                      <div class="carousel-container">
                        <div class="carousel-track-container">
                          {pitchResult[activeSlide] && (
                            <div class="pitch-slide">
                              <div class="slide-header">
                                <span class="slide-num">Slide {pitchResult[activeSlide].slide_number}</span>
                                <h3 class="slide-title">{pitchResult[activeSlide].title}</h3>
                              </div>
                              <ul class="slide-bullets">
                                {pitchResult[activeSlide].bullets?.map((b, idx) => (
                                  <li key={idx}>{b}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                        <div class="carousel-controls">
                          <button 
                            class="carousel-btn" 
                            disabled={activeSlide === 0} 
                            onClick={() => setActiveSlide((prev) => Math.max(0, prev - 1))}
                          >
                            <i class="fa-solid fa-chevron-left"></i> Prev
                          </button>
                          <div class="carousel-dots">
                            {pitchResult.map((_, i) => (
                              <div 
                                className={`carousel-dot ${activeSlide === i ? 'active' : ''}`}
                                key={i}
                                onClick={() => setActiveSlide(i)}
                              ></div>
                            ))}
                          </div>
                          <button 
                            class="carousel-btn" 
                            disabled={activeSlide === pitchResult.length - 1} 
                            onClick={() => setActiveSlide((prev) => Math.min(pitchResult.length - 1, prev + 1))}
                          >
                            Next <i class="fa-solid fa-chevron-right"></i>
                          </button>
                        </div>
                      </div>
                    </div>
                    <div class="action-footer">
                      <p class="congrats-text"><i class="fa-solid fa-circle-check"></i> Pipeline complete! You are ready to start building.</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          /* Settings Tab */
          <div class="tab-pane active">
            <div class="card settings-card">
              <div class="card-header">
                <i class="fa-solid fa-gears card-icon"></i>
                <h2>System Configuration</h2>
              </div>
              <p class="card-description">Set up your API keys and toggle the agent execution modes below.</p>
              
              <div class="settings-form">
                <div class="form-group">
                  <label htmlFor="settings-api-key"><i class="fa-solid fa-key text-violet"></i> Groq API Key</label>
                  <input 
                    type="password" 
                    id="settings-api-key" 
                    value={inputKey} 
                    onChange={(e) => setInputKey(e.target.value)}
                    placeholder={config.groq_api_key_set ? "••••••••••••••••" : "gsk_..."}
                  />
                  <span class="help-text">Inputting your key will enable live generation using Groq and LLaMA models.</span>
                </div>

                <div class="form-group row-group">
                  <div class="toggle-label-group">
                    <label for="settings-demo-mode">Demo Mode (Mock Output)</label>
                    <span class="help-text">If enabled, the app runs instantly using pre-cached mock reports without making external LLM API calls.</span>
                  </div>
                  <label class="switch">
                    <input 
                      type="checkbox" 
                      id="settings-demo-mode" 
                      checked={demoModeToggle}
                      onChange={(e) => setDemoModeToggle(e.target.checked)}
                    />
                    <span class="slider round"></span>
                  </label>
                </div>

                <button class="btn btn-primary" onClick={saveSettings}>
                  <i class="fa-solid fa-floppy-disk"></i> Save Settings
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;

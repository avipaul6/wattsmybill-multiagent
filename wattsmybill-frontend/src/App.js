// src/App.js - Complete React Frontend with Bill Analysis + Top 3 Plan Switching
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const styles = {
  container: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #f0f9ff 0%, #ffffff 50%, #f0fdf4 100%)',
    fontFamily: "'Inter', system-ui, -apple-system, sans-serif"
  },
  header: {
    background: 'rgba(255, 255, 255, 0.9)',
    backdropFilter: 'blur(10px)',
    borderBottom: '1px solid rgba(229, 231, 235, 0.5)',
    position: 'sticky',
    top: 0,
    zIndex: 50,
    padding: '1rem 1.5rem'
  },
  headerContent: {
    maxWidth: '72rem',
    margin: '0 auto',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between'
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem'
  },
  logoIcon: {
    width: '2.5rem',
    height: '2.5rem',
    background: 'linear-gradient(135deg, #2563eb, #16a34a)',
    borderRadius: '0.75rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.5rem'
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: '700',
    background: 'linear-gradient(135deg, #2563eb, #16a34a)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    margin: 0
  },
  subtitle: {
    fontSize: '0.875rem',
    color: '#6b7280',
    margin: 0
  },
  main: {
    maxWidth: '72rem',
    margin: '0 auto',
    padding: '3rem 1.5rem'
  },
  heroTitle: {
    fontSize: '3rem',
    fontWeight: '700',
    textAlign: 'center',
    color: '#111827',
    marginBottom: '1.5rem',
    lineHeight: '1.2'
  },
  heroGradientText: {
    background: 'linear-gradient(135deg, #2563eb, #16a34a)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent'
  },
  heroSubtitle: {
    fontSize: '1.25rem',
    textAlign: 'center',
    color: '#6b7280',
    marginBottom: '3rem',
    maxWidth: '32rem',
    marginLeft: 'auto',
    marginRight: 'auto'
  },
  uploadArea: {
    background: 'white',
    border: '3px dashed #d1d5db',
    borderRadius: '1.5rem',
    padding: '3rem 2.5rem',
    textAlign: 'center',
    margin: '2.5rem auto',
    maxWidth: '38rem',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
  },
  uploadAreaSuccess: {
    borderColor: '#16a34a',
    background: '#f0fdf4'
  },
  uploadIcon: {
    fontSize: '3rem',
    marginBottom: '1rem'
  },
  progressContainer: {
    margin: '4rem 0',
    background: 'white',
    borderRadius: '1.5rem',
    padding: '2rem',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
  },
  planCard: {
    background: 'white',
    border: '2px solid #e5e7eb',
    borderRadius: '1rem',
    padding: '1.5rem',
    margin: '1rem 0',
    transition: 'all 0.3s ease',
    cursor: 'pointer'
  },
  planCardBest: {
    borderColor: '#16a34a',
    background: '#f0fdf4',
    position: 'relative'
  },
  bestPlanBadge: {
    position: 'absolute',
    top: '-0.5rem',
    right: '1rem',
    background: '#16a34a',
    color: 'white',
    padding: '0.25rem 0.75rem',
    borderRadius: '1rem',
    fontSize: '0.75rem',
    fontWeight: '600'
  },
  switchButton: {
    background: 'linear-gradient(135deg, #16a34a, #15803d)',
    color: 'white',
    border: 'none',
    borderRadius: '0.75rem',
    padding: '0.75rem 1.5rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    width: '100%',
    marginTop: '1rem',
    fontSize: '1rem'
  },
  confidenceBadge: {
    padding: '0.25rem 0.5rem',
    borderRadius: '0.5rem',
    fontSize: '0.75rem',
    fontWeight: '500',
    display: 'inline-block',
    marginLeft: '0.5rem'
  },
  highConfidence: {
    background: '#dcfce7',
    color: '#166534'
  },
  mediumConfidence: {
    background: '#fef3c7',
    color: '#92400e'
  },
  lowConfidence: {
    background: '#fee2e2',
    color: '#991b1b'
  },
  button: {
    background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
    color: 'white',
    border: 'none',
    padding: '1rem 2rem',
    borderRadius: '0.75rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    fontSize: '1rem',
    width: '100%'
  },
  error: {
    background: '#fef2f2',
    border: '1px solid #fca5a5',
    color: '#dc2626',
    padding: '1rem',
    borderRadius: '0.75rem',
    marginBottom: '1.5rem',
    maxWidth: '32rem',
    margin: '0 auto 1.5rem'
  },
  successMessage: {
    background: '#f0fdf4',
    border: '1px solid #16a34a',
    color: '#166534',
    padding: '1rem',
    borderRadius: '0.75rem',
    marginBottom: '1.5rem',
    textAlign: 'center'
  },
  locationInput: {
    background: 'white',
    border: '1px solid #d1d5db',
    borderRadius: '0.75rem',
    padding: '1rem',
    margin: '1rem auto',
    maxWidth: '38rem',
    display: 'flex',
    gap: '1rem',
    alignItems: 'end'
  },
  input: {
    flex: 1,
    border: '1px solid #d1d5db',
    borderRadius: '0.5rem',
    padding: '0.5rem 0.75rem',
    fontSize: '0.875rem'
  },
  resultCard: {
    background: 'white',
    borderRadius: '1.5rem',
    padding: '2rem',
    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
    border: '1px solid rgba(229, 231, 235, 0.5)',
    margin: '2rem 0'
  },
  footer: {
    textAlign: 'center',
    padding: '2rem',
    borderTop: '1px solid #e5e7eb',
    marginTop: '4rem',
    color: '#6b7280'
  }
};

const WattsMyBillApp = () => {
  const [file, setFile] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [switchSuccess, setSwitchSuccess] = useState(null);
  const [locationInfo, setLocationInfo] = useState({ state: 'QLD', postcode: '' });
  const [agentsAvailable, setAgentsAvailable] = useState(false);
  const fileInputRef = useRef(null);

  const steps = [
    { id: 'upload', label: 'Upload Bill', icon: '📤' },
    { id: 'parsing', label: 'AI Analysis', icon: '🔍' },
    { id: 'market', label: 'Plan Search', icon: '📊' },
    { id: 'savings', label: 'Calculate Savings', icon: '💰' },
    { id: 'complete', label: 'Ready to Switch', icon: '✅' }
  ];

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/../health`);
        setAgentsAvailable(response.data.agents_available);
      } catch (err) {
        console.warn('Could not check agent status');
      }
    };
    checkHealth();
  }, []);

  const handleFileUpload = async (event) => {
    const uploadedFile = event.target.files[0];
    if (uploadedFile) {
      setFile(uploadedFile);
      setError(null);
      setSwitchSuccess(null);
      await startAnalysis(uploadedFile);
    }
  };

  const startAnalysis = async (uploadedFile) => {
    setIsAnalyzing(true);
    setCurrentStep(0);
    setResults(null);
    
    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      formData.append('state', locationInfo.state);
      if (locationInfo.postcode) {
        formData.append('postcode', locationInfo.postcode);
      }

      const response = await axios.post(`${API_BASE_URL}/upload-bill`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const { analysis_id } = response.data;
      pollProgress(analysis_id);
      
    } catch (err) {
      setIsAnalyzing(false);
      
      if (err.response && err.response.status === 400) {
        const errorData = err.response.data.detail;
        if (typeof errorData === 'object') {
          setError({
            message: errorData.error,
            tips: errorData.tips || []
          });
        } else {
          setError({ message: errorData });
        }
      } else {
        setError({ message: 'Failed to start analysis. Please check your connection and try again.' });
      }
    }
  };

  const pollProgress = async (id) => {
    const checkProgress = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/analysis/${id}/status`);
        const { status, progress } = response.data;
        
        setCurrentStep(Math.floor((progress / 100) * steps.length));
        
        if (status === 'completed') {
          const resultsResponse = await axios.get(`${API_BASE_URL}/analysis/${id}/results`);
          setResults(resultsResponse.data);
          setIsAnalyzing(false);
          setCurrentStep(steps.length);
        } else if (status === 'failed') {
          setError({ message: 'Analysis failed - please try uploading your bill again' });
          setIsAnalyzing(false);
        } else {
          setTimeout(checkProgress, 2000);
        }
      } catch (pollError) {
        setError({ message: 'Lost connection to analysis service' });
        setIsAnalyzing(false);
      }
    };
    
    checkProgress();
  };

  const handlePlanSwitch = async (plan) => {
    try {
      setSwitchSuccess(null);
      
      let postcode = locationInfo.postcode;
      if (!postcode && results?.market_research?.research_parameters?.postcode) {
        postcode = results.market_research.research_parameters.postcode;
      }
      
      const response = await axios.post(`${API_BASE_URL}/generate-switch-url`, {
        plan_id: plan.plan_id,
        postcode: postcode,
        retailer: plan.retailer,
        plan_name: plan.plan_name
      });
      
      setSwitchSuccess({
        retailer: plan.retailer,
        plan_name: plan.plan_name,
        savings: plan.annual_savings,
        postcode: response.data.postcode
      });
      
      window.open(response.data.switch_url, '_blank');
      
    } catch (err) {
      console.error('Failed to generate switch URL:', err);
      
      const fallbackPostcode = results?.market_research?.research_parameters?.postcode || locationInfo.postcode || '2000';
      const fallbackUrl = plan.energy_made_easy_url || 
        `https://www.energymadeeasy.gov.au/plan?id=${plan.plan_id}&postcode=${fallbackPostcode}`;
      
      setSwitchSuccess({
        retailer: plan.retailer,
        plan_name: plan.plan_name,
        savings: plan.annual_savings,
        postcode: fallbackPostcode
      });
      
      window.open(fallbackUrl, '_blank');
    }
  };

  const resetAnalysis = () => {
    setFile(null);
    setCurrentStep(0);
    setIsAnalyzing(false);
    setResults(null);
    setError(null);
    setSwitchSuccess(null);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getConfidenceStyle = (confidence) => {
    switch (confidence) {
      case 'high': return styles.highConfidence;
      case 'medium': return styles.mediumConfidence;
      case 'low': return styles.lowConfidence;
      default: return styles.mediumConfidence;
    }
  };

  const renderPlanCard = (plan, index, isBest = false) => (
    <div 
      key={plan.plan_id || index}
      style={{
        ...styles.planCard,
        ...(isBest ? styles.planCardBest : {})
      }}
    >
      {isBest && <div style={styles.bestPlanBadge}>💡 Best Option</div>}
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
        <div>
          <h4 style={{ margin: '0 0 0.25rem 0', fontSize: '1.125rem', fontWeight: '600', color: '#111827' }}>
            {plan.retailer}
          </h4>
          <p style={{ margin: '0', color: '#6b7280', fontSize: '0.875rem' }}>
            {plan.plan_name}
          </p>
        </div>
        {plan.switch_confidence && (
          <span style={{...styles.confidenceBadge, ...getConfidenceStyle(plan.switch_confidence)}}>
            {plan.switch_confidence} confidence
          </span>
        )}
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
        <div>
          <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>Annual Cost</span>
          <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#111827' }}>
            {formatCurrency(plan.estimated_annual_cost)}
          </div>
        </div>
        <div>
          <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>Annual Savings</span>
          <div style={{ fontSize: '1.25rem', fontWeight: '600', color: plan.annual_savings > 0 ? '#16a34a' : '#6b7280' }}>
            {plan.annual_savings > 0 ? `${formatCurrency(plan.annual_savings)}` : 'No savings'}
          </div>
        </div>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem', marginBottom: '1rem', fontSize: '0.875rem' }}>
        <div>
          <span style={{ color: '#6b7280' }}>Usage Rate</span>
          <div style={{ fontWeight: '500' }}>${plan.usage_rate}/kWh</div>
        </div>
        <div>
          <span style={{ color: '#6b7280' }}>Daily Supply</span>
          <div style={{ fontWeight: '500' }}>${plan.supply_charge_daily}/day</div>
        </div>
        <div>
          <span style={{ color: '#6b7280' }}>Solar Rate</span>
          <div style={{ fontWeight: '500' }}>${plan.solar_feed_in_tariff}/kWh</div>
        </div>
      </div>
      
      {plan.key_features && plan.key_features.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>Key Features:</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
            {plan.key_features.slice(0, 3).map((feature, idx) => (
              <span key={idx} style={{
                background: '#f3f4f6',
                color: '#374151',
                padding: '0.25rem 0.5rem',
                borderRadius: '0.25rem',
                fontSize: '0.75rem'
              }}>
                {feature}
              </span>
            ))}
          </div>
        </div>
      )}
      
      <button
        style={styles.switchButton}
        onClick={() => handlePlanSwitch(plan)}
        onMouseEnter={(e) => {
          e.target.style.transform = 'translateY(-1px)';
          e.target.style.boxShadow = '0 4px 12px rgba(22, 163, 74, 0.3)';
        }}
        onMouseLeave={(e) => {
          e.target.style.transform = 'translateY(0)';
          e.target.style.boxShadow = 'none';
        }}
      >
        🔄 Switch to This Plan
      </button>
      
      <div style={{ 
        fontSize: '0.75rem', 
        color: '#9ca3af', 
        textAlign: 'center', 
        marginTop: '0.5rem' 
      }}>
        Opens Energy Made Easy for postcode {plan.postcode_used || results?.market_research?.research_parameters?.postcode || '2000'}
      </div>
    </div>
  );

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={styles.headerContent}>
          <div style={styles.logo}>
            <div style={styles.logoIcon}>⚡</div>
            <div>
              <h1 style={styles.title}>WattsMyBill</h1>
              <p style={styles.subtitle}>
                {agentsAvailable ? 'AI-Powered Energy Analysis' : 'Smart Energy Analysis'}
              </p>
            </div>
          </div>
          <a 
            href="https://github.com/avipaul6/wattsmybill-multiagent" 
            target="_blank" 
            rel="noopener noreferrer"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: '#6b7280',
              textDecoration: 'none',
              fontSize: '0.875rem',
              padding: '0.5rem 1rem',
              borderRadius: '0.5rem',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#f3f4f6';
              e.target.style.color = '#111827';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = 'transparent';
              e.target.style.color = '#6b7280';
            }}
          >
            <span>Source Code</span>
          </a>
        </div>
      </div>

      <div style={styles.main}>
        <div style={{textAlign: 'center', marginBottom: '4rem'}}>
          <h2 style={styles.heroTitle}>
            What's Really Going On<br />
            <span style={styles.heroGradientText}>With Your Energy Bill?</span>
          </h2>
          <p style={styles.heroSubtitle}>
            {agentsAvailable 
              ? "AI agents analyze your bill and find better energy plans with real switching links."
              : "Smart analysis to find better energy plans and save you money."
            }
          </p>

          {!results && (
            <div style={styles.locationInput}>
              <div style={{flex: 1}}>
                <label style={{fontSize: '0.875rem', color: '#6b7280', display: 'block', marginBottom: '0.25rem'}}>
                  Your State (if not detected from bill)
                </label>
                <select 
                  style={styles.input}
                  value={locationInfo.state}
                  onChange={(e) => setLocationInfo(prev => ({...prev, state: e.target.value}))}
                >
                  <option value="NSW">New South Wales</option>
                  <option value="QLD">Queensland</option>
                  <option value="VIC">Victoria</option>
                  <option value="SA">South Australia</option>
                  <option value="WA">Western Australia</option>
                  <option value="TAS">Tasmania</option>
                  <option value="ACT">ACT</option>
                  <option value="NT">Northern Territory</option>
                </select>
              </div>
              <div style={{flex: 1}}>
                <label style={{fontSize: '0.875rem', color: '#6b7280', display: 'block', marginBottom: '0.25rem'}}>
                  Postcode (if not on bill)
                </label>
                <input 
                  style={styles.input}
                  type="text"
                  placeholder="e.g. 4000"
                  value={locationInfo.postcode}
                  onChange={(e) => setLocationInfo(prev => ({...prev, postcode: e.target.value}))}
                />
              </div>
            </div>
          )}

          {results?.market_research?.research_parameters?.postcode && (
            <div style={{
              background: '#f0fdf4',
              border: '1px solid #16a34a',
              color: '#166534',
              padding: '0.75rem',
              borderRadius: '0.75rem',
              marginBottom: '1rem',
              fontSize: '0.875rem',
              textAlign: 'center'
            }}>
              📍 Postcode {results.market_research.research_parameters.postcode} extracted from your bill
            </div>
          )}

          {switchSuccess && (
            <div style={styles.successMessage}>
              <strong>🎉 Great choice!</strong> You're switching to {switchSuccess.retailer} {switchSuccess.plan_name}.
              <br />
              <span style={{fontSize: '0.875rem'}}>
                Potential annual savings: {formatCurrency(switchSuccess.savings)} 
                • Using postcode: {switchSuccess.postcode}
                • Energy Made Easy will guide you through the official switching process.
              </span>
            </div>
          )}
          
          {error && (
            <div style={styles.error}>
              <strong>❌ {error.message}</strong>
              {error.tips && error.tips.length > 0 && (
                <div style={{marginTop: '0.5rem'}}>
                  <strong>Tips:</strong>
                  <ul style={{margin: '0.5rem 0', paddingLeft: '1.5rem', textAlign: 'left'}}>
                    {error.tips.map((tip, idx) => (
                      <li key={idx} style={{fontSize: '0.875rem'}}>{tip}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <div 
            style={{
              ...styles.uploadArea,
              ...(file ? styles.uploadAreaSuccess : {})
            }}
            onClick={() => fileInputRef.current?.click()}
            onMouseEnter={(e) => {
              if (!file && !isAnalyzing) {
                e.target.style.borderColor = '#3b82f6';
                e.target.style.background = '#f8faff';
                e.target.style.transform = 'translateY(-2px)';
              }
            }}
            onMouseLeave={(e) => {
              e.target.style.borderColor = file ? '#16a34a' : '#d1d5db';
              e.target.style.background = file ? '#f0fdf4' : 'white';
              e.target.style.transform = 'translateY(0)';
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileUpload}
              style={{display: 'none'}}
              disabled={isAnalyzing}
            />
            
            <div style={styles.uploadIcon}>
              {file ? '✅' : isAnalyzing ? '⏳' : '📤'}
            </div>
            
            <h3 style={{fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem'}}>
              {file ? file.name : isAnalyzing ? 'Analyzing...' : 'Upload your Australian energy bill'}
            </h3>
            <p style={{color: '#6b7280', margin: 0}}>
              {file ? (isAnalyzing ? 'Analysis in progress...' : 'Ready for analysis!') : 'PDF or image files supported'}
            </p>
          </div>
        </div>

        {(isAnalyzing || results) && (
          <div style={styles.progressContainer}>
            <h3 style={{textAlign: 'center', marginBottom: '2rem'}}>
              {agentsAvailable ? 'AI Agent Analysis Progress' : 'Analysis Progress'}
            </h3>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '1rem'
            }}>
              {steps.map((step, index) => {
                const isCompleted = currentStep > index;
                const isCurrent = currentStep === index && isAnalyzing;
                
                return (
                  <div key={step.id} style={{
                    flex: 1,
                    minWidth: '120px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center'
                  }}>
                    <div style={{
                      width: '3rem',
                      height: '3rem',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginBottom: '0.75rem',
                      fontSize: '1.5rem',
                      transition: 'all 0.5s ease',
                      ...(isCompleted ? {
                        background: '#16a34a',
                        color: 'white',
                        transform: 'scale(1.1)'
                      } : isCurrent ? {
                        background: '#3b82f6',
                        color: 'white',
                        transform: 'scale(1.1)'
                      } : {
                        background: '#e5e7eb',
                        color: '#9ca3af'
                      })
                    }}>
                      {isCompleted ? '✅' : step.icon}
                    </div>
                    <span style={{
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      color: isCompleted || isCurrent ? '#111827' : '#9ca3af',
                      textAlign: 'center'
                    }}>
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {results && (
          <>
            {results.market_research?.top_switching_plans && results.market_research.top_switching_plans.length > 0 && (
              <div style={{marginBottom: '4rem'}}>
                <h3 style={{textAlign: 'center', marginBottom: '1.5rem', fontSize: '2rem', fontWeight: '700'}}>
                  🔄 Top 3 Plans to Switch To
                </h3>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
                  gap: '1.5rem'
                }}>
                  {results.market_research.top_switching_plans.map((plan, index) => 
                    renderPlanCard(plan, index, index === 0)
                  )}
                </div>
              </div>
            )}

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '2rem',
              margin: '4rem 0'
            }}>
              
              {results.bill_analysis?.bill_data && (
                <div style={styles.resultCard}>
                  <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem'}}>
                    <div style={{
                      width: '2.5rem',
                      height: '2.5rem',
                      background: '#dbeafe',
                      borderRadius: '0.75rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1.25rem'
                    }}>📄</div>
                    <h3 style={{fontSize: '1.25rem', fontWeight: '600', color: '#111827', margin: 0}}>
                      Your Energy Bill
                    </h3>
                  </div>
                  
                  {(() => {
                    const billData = results.bill_analysis.bill_data;
                    const annualUsage = billData.usage_kwh * (365 / (billData.billing_days || 90));
                    const annualCost = billData.total_amount * (365 / (billData.billing_days || 90));
                    
                    return (
                      <>
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Current Retailer</span>
                          <strong>{billData.retailer || 'Unknown'}</strong>
                        </div>
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Annual Usage</span>
                          <strong>{Math.round(annualUsage).toLocaleString()} kWh</strong>
                        </div>
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Annual Cost</span>
                          <strong>{formatCurrency(annualCost)}</strong>
                        </div>
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>State</span>
                          <strong>{billData.state || 'Unknown'}</strong>
                        </div>
                        {billData.has_solar && (
                          <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                            <span>Solar System</span>
                            <strong style={{color: '#16a34a'}}>✅ Installed</strong>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
              )}

              {results.market_research?.market_insights && (
                <div style={styles.resultCard}>
                  <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem'}}>
                    <div style={{
                      width: '2.5rem',
                      height: '2.5rem',
                      background: '#ecfdf5',
                      borderRadius: '0.75rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1.25rem'
                    }}>📈</div>
                    <h3 style={{fontSize: '1.25rem', fontWeight: '600', color: '#111827', margin: 0}}>
                      Market Analysis
                    </h3>
                  </div>
                  
                  {(() => {
                    const insights = results.market_research.market_insights;
                    
                    return (
                      <>
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Your Rate Position</span>
                          <strong style={{
                            color: insights.market_position === 'excellent' ? '#16a34a' : 
                                  insights.market_position === 'competitive' ? '#f59e0b' : '#dc2626'
                          }}>
                            {insights.market_position?.charAt(0).toUpperCase() + insights.market_position?.slice(1)}
                          </strong>
                        </div>
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Current Rate</span>
                          <strong>${insights.current_rate_per_kwh}/kWh</strong>
                        </div>
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>State Average</span>
                          <strong>${insights.state_average_rate}/kWh</strong>
                        </div>
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Plans Analyzed</span>
                          <strong>{insights.plans_found}</strong>
                        </div>
                        
                        {insights.market_trends && (
                          <div style={{
                            marginTop: '1rem',
                            padding: '0.75rem',
                            background: '#f8fafc',
                            borderRadius: '0.5rem',
                            fontSize: '0.875rem'
                          }}>
                            <strong>Market Trends:</strong>
                            <ul style={{margin: '0.5rem 0', paddingLeft: '1rem'}}>
                              {insights.market_trends.slice(0, 2).map((trend, idx) => (
                                <li key={idx}>{trend}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
              )}

              {results.market_research?.usage_optimization && (
                <div style={styles.resultCard}>
                  <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem'}}>
                    <div style={{
                      width: '2.5rem',
                      height: '2.5rem',
                      background: '#fef3c7',
                      borderRadius: '0.75rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1.25rem'
                    }}>💡</div>
                    <h3 style={{fontSize: '1.25rem', fontWeight: '600', color: '#111827', margin: 0}}>
                      Usage Optimization
                    </h3>
                  </div>
                  
                  {(() => {
                    const usage = results.market_research.usage_optimization;
                    
                    return (
                      <>
                        <div style={{marginBottom: '1rem'}}>
                          <strong style={{color: '#1e40af'}}>{usage.usage_advice}</strong>
                        </div>
                        
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Usage Category</span>
                          <strong style={{
                            color: usage.usage_category === 'low' ? '#16a34a' : 
                                  usage.usage_category === 'average' ? '#f59e0b' : '#dc2626'
                          }}>
                            {usage.usage_category?.charAt(0).toUpperCase() + usage.usage_category?.slice(1)}
                          </strong>
                        </div>
                        
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Efficiency Savings Potential</span>
                          <strong>{formatCurrency(usage.estimated_efficiency_savings)}/year</strong>
                        </div>
                        
                        {usage.priority_actions && (
                          <div style={{
                            marginTop: '1rem',
                            padding: '0.75rem',
                            background: '#fffbeb',
                            borderRadius: '0.5rem',
                            fontSize: '0.875rem'
                          }}>
                            <strong>Priority Actions:</strong>
                            <ul style={{margin: '0.5rem 0', paddingLeft: '1rem'}}>
                              {usage.priority_actions.map((action, idx) => (
                                <li key={idx}>{action}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
              )}

              {results.market_research?.solar_analysis && (
                <div style={styles.resultCard}>
                  <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem'}}>
                    <div style={{
                      width: '2.5rem',
                      height: '2.5rem',
                      background: '#fef3c7',
                      borderRadius: '0.75rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1.25rem'
                    }}>☀️</div>
                    <h3 style={{fontSize: '1.25rem', fontWeight: '600', color: '#111827', margin: 0}}>
                      Solar Analysis
                    </h3>
                  </div>
                  
                  {(() => {
                    const solar = results.market_research.solar_analysis;
                    
                    return (
                      <>
                        {solar.has_solar ? (
                          <>
                            <div style={{marginBottom: '1rem'}}>
                              <strong style={{color: '#16a34a'}}>✅ {solar.analysis}</strong>
                            </div>
                            
                            <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                              <span>Annual Export</span>
                              <strong>{solar.estimated_annual_export?.toLocaleString()} kWh</strong>
                            </div>
                            
                            <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                              <span>Total Generation</span>
                              <strong>{solar.estimated_total_generation?.toLocaleString()} kWh</strong>
                            </div>
                            
                            {solar.optimization_tips && (
                              <div style={{
                                marginTop: '1rem',
                                padding: '0.75rem',
                                background: '#f0fdf4',
                                borderRadius: '0.5rem',
                                fontSize: '0.875rem'
                              }}>
                                <strong>Optimization Tips:</strong>
                                <ul style={{margin: '0.5rem 0', paddingLeft: '1rem'}}>
                                  {solar.optimization_tips.slice(0, 3).map((tip, idx) => (
                                    <li key={idx}>{tip}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </>
                        ) : (
                          <>
                            <div style={{marginBottom: '1rem'}}>
                              <strong style={{color: solar.solar_suitable ? '#f59e0b' : '#6b7280'}}>
                                {solar.solar_suitable ? '💡 Solar could be beneficial' : 'ℹ️ Solar may not be cost-effective'}
                              </strong>
                            </div>
                            
                            {solar.solar_suitable && (
                              <>
                                <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                                  <span>Recommended System</span>
                                  <strong>{solar.recommended_system_size}</strong>
                                </div>
                                
                                <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                                  <span>Potential Savings</span>
                                  <strong>{formatCurrency(solar.estimated_annual_savings)}/year</strong>
                                </div>
                                
                                <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                                  <span>Payback Period</span>
                                  <strong>{solar.payback_period}</strong>
                                </div>
                              </>
                            )}
                            
                            {solar.next_steps && (
                              <div style={{
                                marginTop: '1rem',
                                padding: '0.75rem',
                                background: solar.solar_suitable ? '#fffbeb' : '#f8fafc',
                                borderRadius: '0.5rem',
                                fontSize: '0.875rem'
                              }}>
                                <strong>Next Steps:</strong>
                                <ul style={{margin: '0.5rem 0', paddingLeft: '1rem'}}>
                                  {solar.next_steps.slice(0, 3).map((step, idx) => (
                                    <li key={idx}>{step}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </>
                        )}
                      </>
                    );
                  })()}
                </div>
              )}

              {results.market_research?.savings_analysis && (
                <div style={styles.resultCard}>
                  <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem'}}>
                    <div style={{
                      width: '2.5rem',
                      height: '2.5rem',
                      background: '#dcfce7',
                      borderRadius: '0.75rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1.25rem'
                    }}>💰</div>
                    <h3 style={{fontSize: '1.25rem', fontWeight: '600', color: '#111827', margin: 0}}>
                      Savings Summary
                    </h3>
                  </div>
                  
                  {(() => {
                    const savings = results.market_research.savings_analysis;
                    
                    return (
                      <>
                        <div style={{textAlign: 'center', marginBottom: '1.5rem'}}>
                          <div style={{fontSize: '2rem', fontWeight: '700', color: '#16a34a', marginBottom: '0.5rem'}}>
                            {formatCurrency(savings.max_annual_savings)}
                          </div>
                          <div style={{fontSize: '0.875rem', color: '#6b7280'}}>Maximum Annual Savings</div>
                        </div>
                        
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Quarterly Savings</span>
                          <strong>{formatCurrency(savings.max_quarterly_savings)}</strong>
                        </div>
                        
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Better Plans Found</span>
                          <strong>{savings.better_plans_available}</strong>
                        </div>
                        
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Savings Potential</span>
                          <strong style={{
                            color: savings.savings_potential === 'high' ? '#16a34a' : 
                                  savings.savings_potential === 'medium' ? '#f59e0b' : 
                                  savings.savings_potential === 'low' ? '#dc2626' : '#6b7280'
                          }}>
                            {savings.savings_potential?.charAt(0).toUpperCase() + savings.savings_potential?.slice(1)}
                          </strong>
                        </div>
                        
                        <div style={{
                          marginTop: '1.5rem',
                          padding: '1rem',
                          background: '#f0fdf4',
                          borderRadius: '0.75rem',
                          textAlign: 'center'
                        }}>
                          <strong style={{color: '#166534'}}>
                            {savings.savings_message}
                          </strong>
                        </div>
                      </>
                    );
                  })()}
                </div>
              )}
            </div>

            {results.market_research?.recommended_plans && results.market_research.recommended_plans.length > 3 && (
              <div style={{marginBottom: '3rem'}}>
                <h3 style={{textAlign: 'center', marginBottom: '1.5rem', fontSize: '1.5rem', fontWeight: '600'}}>
                  📊 Other Available Plans
                </h3>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
                  gap: '1.5rem'
                }}>
                  {results.market_research.recommended_plans
                    .slice(3, 9)
                    .map((plan, index) => renderPlanCard(plan, index + 3))
                  }
                </div>
              </div>
            )}

            {results.market_research?.savings_analysis?.savings_potential === 'none' && (
              <div style={styles.resultCard}>
                <div style={{textAlign: 'center'}}>
                  <div style={{fontSize: '3rem', marginBottom: '1rem'}}>✅</div>
                  <h3 style={{marginBottom: '1rem', color: '#16a34a'}}>Great News!</h3>
                  <p style={{fontSize: '1.125rem', color: '#6b7280'}}>
                    Your current energy plan is already competitive with the market. 
                    You're getting a good deal!
                  </p>
                </div>
              </div>
            )}
          </>
        )}

        {(results || error) && (
          <div style={{textAlign: 'center', marginTop: '3rem'}}>
            <button 
              onClick={resetAnalysis}
              style={{
                ...styles.button,
                fontSize: '1.125rem',
                padding: '1.25rem 2.5rem',
                width: 'auto',
                maxWidth: '300px',
                margin: '0 auto'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 8px 25px rgba(59, 130, 246, 0.3)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = 'none';
              }}
            >
              Analyze Another Bill
            </button>
          </div>
        )}
      </div>

      <div style={styles.footer}>
        <p>
          {agentsAvailable 
            ? "Powered by AI Agents + Live Australian Energy Market Data"
            : "Powered by Smart Analysis + Australian Energy Market Data"
          }
        </p>
        <p style={{fontSize: '0.875rem', marginTop: '0.5rem'}}>
          <a 
            href="https://github.com/avipaul6/wattsmybill-multiagent" 
            target="_blank" 
            rel="noopener noreferrer"
            style={{color: '#3b82f6', textDecoration: 'none'}}
          >
            View Source Code on GitHub
          </a>
        </p>
      </div>
    </div>
  );
};

export default WattsMyBillApp;
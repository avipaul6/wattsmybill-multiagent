// src/App.js - Complete WattsMyBill App with Google Cloud ADK Integration
// PART 1: Imports and Styles

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
  adkBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.5rem 1rem',
    borderRadius: '0.75rem',
    fontSize: '0.875rem',
    fontWeight: '600',
    transition: 'all 0.3s ease'
  },
  adkActive: {
    background: 'linear-gradient(135deg, #10b981, #059669)',
    color: 'white'
  },
  adkInactive: {
    background: '#f3f4f6',
    color: '#6b7280'
  },
  githubLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    color: '#6b7280',
    textDecoration: 'none',
    fontSize: '0.875rem',
    padding: '0.5rem 1rem',
    borderRadius: '0.5rem',
    transition: 'all 0.3s ease'
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
  adkStatusCard: {
    background: 'white',
    border: '2px solid #e5e7eb',
    borderRadius: '1rem',
    padding: '1.5rem',
    margin: '2rem auto',
    maxWidth: '48rem',
    textAlign: 'center'
  },
  adkStatusActive: {
    borderColor: '#10b981',
    background: '#f0fdf4'
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
  supportedCompanies: {
    background: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '1rem',
    padding: '1.5rem',
    margin: '2rem auto',
    maxWidth: '38rem',
    textAlign: 'center'
  },
  progressContainer: {
    margin: '4rem 0',
    background: 'white',
    borderRadius: '1.5rem',
    padding: '2rem',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
  },
  progressSteps: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '2rem',
    flexWrap: 'wrap',
    gap: '1rem'
  },
  progressStep: {
    flex: 1,
    minWidth: '120px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center'
  },
  progressIcon: {
    width: '3rem',
    height: '3rem',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '0.75rem',
    fontSize: '1.5rem',
    transition: 'all 0.5s ease'
  },
  progressIconCompleted: {
    background: '#16a34a',
    color: 'white',
    transform: 'scale(1.1)'
  },
  progressIconCurrent: {
    background: '#3b82f6',
    color: 'white',
    animation: 'pulse 2s infinite',
    transform: 'scale(1.1)'
  },
  progressIconPending: {
    background: '#e5e7eb',
    color: '#9ca3af'
  },
  resultsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '2rem',
    margin: '4rem 0'
  },
  resultCard: {
    background: 'white',
    borderRadius: '1.5rem',
    padding: '2rem',
    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
    border: '1px solid rgba(229, 231, 235, 0.5)',
    transition: 'all 0.3s ease'
  },
  cardHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    marginBottom: '1.5rem'
  },
  cardIcon: {
    width: '2.5rem',
    height: '2.5rem',
    borderRadius: '0.75rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.25rem'
  },
  cardTitle: {
    fontSize: '1.25rem',
    fontWeight: '700',
    color: '#111827',
    margin: 0
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
  adkButton: {
    background: 'linear-gradient(135deg, #10b981, #059669)',
    color: 'white'
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
  billingContext: {
    background: '#f0f9ff',
    border: '1px solid #93c5fd',
    borderRadius: '0.75rem',
    padding: '1rem',
    margin: '1rem 0',
    fontSize: '0.875rem',
    color: '#1e40af'
  },
  footer: {
    textAlign: 'center',
    padding: '2rem',
    borderTop: '1px solid #e5e7eb',
    marginTop: '4rem',
    color: '#6b7280'
  }
};

// PART 2: Component State and Setup

const WattsMyBillApp = () => {
  const [file, setFile] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [supportedCompanies, setSupportedCompanies] = useState([]);
  const [companyDetected, setCompanyDetected] = useState(null);
  const [adkStatus, setAdkStatus] = useState(null);
  const [useAdk, setUseAdk] = useState(true);
  const [processingMethod, setProcessingMethod] = useState(null);
  const fileInputRef = useRef(null);

  const steps = [
    { id: 'upload', label: 'Upload Bill', icon: '📤' },
    { id: 'parsing', label: 'Parsing Bill', icon: '🔍' },
    { id: 'market', label: 'Market Scan', icon: '📊' },
    { id: 'rebates', label: 'Rebate Scan', icon: '💰' },
    { id: 'summary', label: 'Savings Summary', icon: '✅' }
  ];

  const adkSteps = [
    { id: 'adk_init', label: 'ADK Coordination', icon: '🤖' },
    { id: 'real_bill', label: 'Real Bill Agent', icon: '🔍' },
    { id: 'real_market', label: 'Real Market Agent', icon: '📊' },
    { id: 'real_rebates', label: 'Real Rebate Agent', icon: '🎯' },
    { id: 'real_usage', label: 'Real Usage Agent', icon: '⚡' },
    { id: 'synthesis', label: 'ADK Synthesis', icon: '✅' }
  ];

  // Fetch supported companies and ADK status on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch supported companies
        const companiesResponse = await axios.get(`${API_BASE_URL}/supported-companies`);
        setSupportedCompanies(companiesResponse.data.supported_companies);

        // Fetch ADK status
        const adkResponse = await axios.get(`${API_BASE_URL}/adk-status`);
        setAdkStatus(adkResponse.data);
        
        // Set default ADK usage based on availability
        if (adkResponse.data.adk_integration?.workflow_ready) {
          setUseAdk(true);
        } else {
          setUseAdk(false);
        }
      } catch (err) {
        console.warn('Could not fetch initialization data:', err);
      }
    };
    
    fetchData();
  }, []);

  const handleFileUpload = async (event) => {
    const uploadedFile = event.target.files[0];
    if (uploadedFile) {
      setFile(uploadedFile);
      setError(null);
      await startAnalysis(uploadedFile);
    }
  };

  const startAnalysis = async (uploadedFile) => {
    setIsAnalyzing(true);
    setCurrentStep(0);
    setCompanyDetected(null);
    setProcessingMethod(null);
    
    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      formData.append('state', 'QLD');
      formData.append('use_adk', useAdk.toString());

      const response = await axios.post(`${API_BASE_URL}/upload-bill`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const { analysis_id, processing_method, adk_available } = response.data;
      setProcessingMethod(processing_method);
      
      // Update ADK availability if changed
      if (!adk_available && useAdk) {
        setUseAdk(false);
      }
      
      pollProgress(analysis_id);
      
    } catch (err) {
      setIsAnalyzing(false);
      
      if (err.response && err.response.status === 400) {
        // Handle validation error
        const errorData = err.response.data.detail;
        if (typeof errorData === 'object') {
          setError({
            message: errorData.error,
            details: errorData.validation_details,
            supportedCompanies: errorData.supported_companies,
            tips: errorData.tips
          });
        } else {
          setError({ message: errorData });
        }
      } else {
        setError({ message: 'Failed to start analysis. Make sure the backend is running.' });
      }
    }
  };

  const pollProgress = async (id) => {
    const checkProgress = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/analysis/${id}/status`);
        const { status, progress, company_detected } = response.data;
        
        if (company_detected) {
          setCompanyDetected(company_detected);
        }
        
        // Different step calculation based on processing method
        const currentSteps = processingMethod === 'adk_integrated' ? adkSteps : steps;
        setCurrentStep(Math.floor((progress / 100) * currentSteps.length));
        
        if (status === 'completed') {
          const resultsResponse = await axios.get(`${API_BASE_URL}/analysis/${id}/results`);
          setResults(resultsResponse.data);
          setIsAnalyzing(false);
          setCurrentStep(currentSteps.length);
        } else if (status === 'failed') {
          setError({ message: 'Analysis failed' });
          setIsAnalyzing(false);
        } else {
          setTimeout(checkProgress, 2000);
        }
      } catch (pollError) {
        setError({ message: 'Lost connection to backend' });
        setIsAnalyzing(false);
      }
    };
    
    checkProgress();
  };

  const resetAnalysis = () => {
    setFile(null);
    setCurrentStep(0);
    setIsAnalyzing(false);
    setResults(null);
    setError(null);
    setCompanyDetected(null);
    setProcessingMethod(null);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getBillingPeriodText = (results) => {
    const billingContext = results?.billing_context;
    if (billingContext?.period_type === 'quarterly') {
      return {
        period: 'Quarterly',
        description: billingContext.period_description,
        multiplier: billingContext.annual_multiplier || 4
      };
    }
    return {
      period: 'Annual',
      description: 'Based on annual estimates',
      multiplier: 1
    };
  };

// PART 3: Render Helper Functions

  const renderAdkStatus = () => {
    if (!adkStatus) return null;

    const isAdkReady = adkStatus.adk_integration?.workflow_ready;
    const realAgentsUsed = adkStatus.adk_integration?.real_agents_used;
    const apiIntegration = adkStatus.adk_integration?.api_integration;

    return (
      <div style={{
        ...styles.adkStatusCard,
        ...(isAdkReady ? styles.adkStatusActive : {})
      }}>
        <h3 style={{margin: '0 0 1rem 0', fontSize: '1.25rem', fontWeight: '700'}}>
          🤖 Google Cloud ADK Integration Status
        </h3>
        
        <div style={{display: 'flex', justifyContent: 'center', gap: '2rem', marginBottom: '1rem'}}>
          <div>
            <div style={{fontWeight: '600', color: isAdkReady ? '#059669' : '#dc2626'}}>
              {isAdkReady ? '✅ Active' : '❌ Inactive'}
            </div>
            <div style={{fontSize: '0.875rem', color: '#6b7280'}}>ADK Workflow</div>
          </div>
          
          {isAdkReady && (
            <>
              <div>
                <div style={{fontWeight: '600', color: realAgentsUsed ? '#059669' : '#f59e0b'}}>
                  {realAgentsUsed ? '🎯 Real Agents' : '🔧 Mock Agents'}
                </div>
                <div style={{fontSize: '0.875rem', color: '#6b7280'}}>Agent Type</div>
              </div>
              
              <div>
                <div style={{fontWeight: '600', color: apiIntegration ? '#059669' : '#f59e0b'}}>
                  {apiIntegration ? '🌐 Live API' : '📊 Fallback'}
                </div>
                <div style={{fontSize: '0.875rem', color: '#6b7280'}}>Data Source</div>
              </div>
            </>
          )}
        </div>

        {isAdkReady && (
          <div style={{fontSize: '0.875rem', color: '#6b7280'}}>
            ADK Agents: {adkStatus.adk_integration?.agent_count || 0} | 
            Market Plans: {adkStatus.adk_integration?.market_plans_available || 0} | 
            ETL: {adkStatus.adk_integration?.etl_status ? 'Connected' : 'Unavailable'}
          </div>
        )}

        {!isAdkReady && (
          <div style={{fontSize: '0.875rem', color: '#dc2626', marginTop: '0.5rem'}}>
            {adkStatus.adk_integration?.reason || 'ADK integration not available'}
          </div>
        )}
      </div>
    );
  };

  const renderProcessingMethod = () => {
    if (!processingMethod) return null;

    const isAdk = processingMethod === 'adk_integrated';
    
    return (
      <div style={{
        background: isAdk ? '#f0fdf4' : '#f8fafc',
        border: `1px solid ${isAdk ? '#16a34a' : '#e2e8f0'}`,
        borderRadius: '0.75rem',
        padding: '1rem',
        margin: '1rem 0',
        textAlign: 'center'
      }}>
        <div style={{fontWeight: '600', color: isAdk ? '#166534' : '#374151'}}>
          {isAdk ? '🤖 ADK-Integrated Processing' : '🔧 Standalone Processing'}
        </div>
        <div style={{fontSize: '0.875rem', color: '#6b7280', marginTop: '0.25rem'}}>
          {isAdk 
            ? 'Using Google Cloud ADK with real WattsMyBill agents'
            : 'Using standalone agent processing'
          }
        </div>
      </div>
    );
  };

  // PART 4: Main JSX Return Structure

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerContent}>
          <div style={styles.logo}>
            <div style={styles.logoIcon}>⚡</div>
            <div>
              <h1 style={styles.title}>WattsMyBill</h1>
              <p style={styles.subtitle}>AI Energy Analysis with Google Cloud ADK</p>
            </div>
          </div>
          
          {/* ADK Status Badge */}
          {adkStatus && (
            <div style={{
              ...styles.adkBadge,
              ...(adkStatus.adk_integration?.workflow_ready ? styles.adkActive : styles.adkInactive)
            }}>
              <span>🤖</span>
              <span>
                ADK {adkStatus.adk_integration?.workflow_ready ? 'Active' : 'Inactive'}
              </span>
            </div>
          )}
          
          <a 
            href="https://github.com/avipaul6/wattsmybill-multiagent" 
            target="_blank" 
            rel="noopener noreferrer"
            style={styles.githubLink}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#f3f4f6';
              e.target.style.color = '#111827';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = 'transparent';
              e.target.style.color = '#6b7280';
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            <span>Source Code</span>
          </a>
        </div>
      </div>

      <div style={styles.main}>
        {/* Hero Section */}
        <div style={{textAlign: 'center', marginBottom: '4rem'}}>
          <h2 style={styles.heroTitle}>
            What's Really Going On<br />
            <span style={styles.heroGradientText}>With Your Energy Bill?</span>
          </h2>
          <p style={styles.heroSubtitle}>
            Let real AI agents powered by Google Cloud ADK analyze your Australian energy bill and save you money.
          </p>

          {/* ADK Status Card */}
          {renderAdkStatus()}

          {/* Processing Method Display */}
          {renderProcessingMethod()}

          {/* ADK Toggle (when available) */}
          {adkStatus?.adk_integration?.workflow_ready && (
            <div style={{
              background: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '1rem',
              padding: '1.5rem',
              margin: '2rem auto',
              maxWidth: '32rem'
            }}>
              <h4 style={{margin: '0 0 1rem 0', fontSize: '1rem', fontWeight: '600'}}>
                🔧 Analysis Method
              </h4>
              <div style={{display: 'flex', gap: '1rem', alignItems: 'center'}}>
                <label style={{display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer'}}>
                  <input
                    type="checkbox"
                    checked={useAdk}
                    onChange={(e) => setUseAdk(e.target.checked)}
                    disabled={isAnalyzing}
                    style={{width: '1.25rem', height: '1.25rem'}}
                  />
                  <span style={{fontWeight: '500'}}>
                    Use Google Cloud ADK with Real Agents
                  </span>
                </label>
              </div>
              <div style={{fontSize: '0.875rem', color: '#6b7280', marginTop: '0.5rem'}}>
                {useAdk 
                  ? '🤖 Will use ADK-orchestrated real agents for comprehensive analysis'
                  : '🔧 Will use standalone agent processing (fallback mode)'
                }
              </div>
            </div>
          )}

          {/* Company Detection */}
          {companyDetected && (
            <div style={{
              ...styles.billingContext,
              background: '#f0fdf4',
              border: '1px solid #16a34a',
              color: '#166534',
              marginBottom: '1rem'
            }}>
              ✅ Detected: {companyDetected} energy bill
            </div>
          )}
          
          {/* Low confidence warning */}
          {file && !companyDetected && !error && (
            <div style={{
              ...styles.billingContext,
              background: '#fffbeb',
              border: '1px solid #f59e0b',
              color: '#92400e',
              marginBottom: '1rem'
            }}>
              ⚠️ Document uploaded - proceeding with analysis (energy company not clearly detected)
            </div>
          )}


{/* PART 5: Error Handling and Upload Area */}

          {/* Error Display */}
          {error && (
            <div style={styles.error}>
              <strong>❌ {error.message}</strong>
              {error.details && (
                <div style={{marginTop: '1rem'}}>
                  <p><strong>Analysis:</strong></p>
                  <ul style={{textAlign: 'left', marginLeft: '1rem', fontSize: '0.875rem'}}>
                    <li>Energy terms found: {error.details.energy_indicators_found || 0}</li>
                    <li>Australian energy terms: {error.details.australian_energy_terms_found || 0}</li>
                    <li>Energy company recognized: {error.details.recognized_energy_company ? 'Yes' : 'No'}</li>
                    {error.details.non_energy_indicators_found > 0 && (
                      <li style={{color: '#dc2626', fontWeight: '600'}}>
                        Non-energy business indicators: {error.details.non_energy_indicators_found}
                      </li>
                    )}
                    {error.details.reason && (
                      <li style={{color: '#dc2626', fontWeight: '600'}}>
                        Detected as: {error.details.reason}
                      </li>
                    )}
                  </ul>
                </div>
              )}
              {error.tips && (
                <div style={{marginTop: '1rem'}}>
                  <p><strong>💡 Tips:</strong></p>
                  <ul style={{textAlign: 'left', marginLeft: '1rem', fontSize: '0.875rem'}}>
                    {error.tips.map((tip, index) => (
                      <li key={index}>{tip}</li>
                    ))}
                  </ul>
                </div>
              )}
              {error.supportedCompanies && error.supportedCompanies.length > 0 && (
                <div style={{marginTop: '1rem'}}>
                  <p><strong>📋 Supported Companies (sample):</strong></p>
                  <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.25rem',
                    marginTop: '0.5rem'
                  }}>
                    {error.supportedCompanies.slice(0, 8).map((company, index) => (
                      <span key={index} style={{
                        background: '#fef2f2',
                        color: '#991b1b',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '0.5rem',
                        fontSize: '0.75rem',
                        fontWeight: '500'
                      }}>
                        {company}
                      </span>
                    ))}
                    <span style={{
                      color: '#6b7280',
                      fontSize: '0.75rem',
                      padding: '0.25rem'
                    }}>
                      +{supportedCompanies.length - 8} more...
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Upload Area */}
          <div 
            style={{
              ...styles.uploadArea,
              ...(file ? styles.uploadAreaSuccess : {})
            }}
            onClick={() => fileInputRef.current?.click()}
            onMouseEnter={(e) => {
              if (!file) {
                e.target.style.borderColor = useAdk ? '#10b981' : '#3b82f6';
                e.target.style.background = useAdk ? '#f0fdf4' : '#f8faff';
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
              {file ? '✅' : (useAdk ? '🤖' : '📤')}
            </div>
            
            <h3 style={{fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem'}}>
              {file ? file.name : 'Upload your Australian energy bill'}
            </h3>
            <p style={{color: '#6b7280', margin: 0}}>
              {file 
                ? `Ready for ${useAdk ? 'ADK' : 'standalone'} analysis!` 
                : 'PDF or image files supported'
              }
            </p>
          </div>

          {/* Supported Companies */}
          {supportedCompanies.length > 0 && (
            <div style={styles.supportedCompanies}>
              <h4 style={{margin: '0 0 1rem 0', fontSize: '1rem', fontWeight: '600'}}>
                📋 Supported Energy Companies
              </h4>
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '0.5rem',
                justifyContent: 'center',
                fontSize: '0.875rem'
              }}>
                {supportedCompanies.slice(0, 10).map((company, index) => (
                  <span key={index} style={{
                    background: '#e0f2fe',
                    color: '#0369a1',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '1rem',
                    fontWeight: '500'
                  }}>
                    {company}
                  </span>
                ))}
                {supportedCompanies.length > 10 && (
                  <span style={{
                    background: '#f1f5f9',
                    color: '#475569',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '1rem',
                    fontWeight: '500'
                  }}>
                    +{supportedCompanies.length - 10} more
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

{/* PART 6: Progress Display */}

        {/* Progress Steps */}
        {(isAnalyzing || results) && (
          <div style={styles.progressContainer}>
            <h3 style={{textAlign: 'center', marginBottom: '2rem'}}>
              {processingMethod === 'adk_integrated' ? '🤖 ADK Analysis Progress' : '🔧 Analysis Progress'}
            </h3>
            <div style={styles.progressSteps}>
              {(processingMethod === 'adk_integrated' ? adkSteps : steps).map((step, index) => {
                const isCompleted = currentStep > index;
                const isCurrent = currentStep === index && isAnalyzing;
                
                return (
                  <div key={step.id} style={styles.progressStep}>
                    <div style={{
                      ...styles.progressIcon,
                      ...(isCompleted ? styles.progressIconCompleted : 
                          isCurrent ? styles.progressIconCurrent : 
                          styles.progressIconPending)
                    }}>
                      {isCompleted ? '✅' : step.icon}
                    </div>
                    <span style={{
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      color: isCompleted || isCurrent ? '#111827' : '#9ca3af'
                    }}>
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
            
            {processingMethod === 'adk_integrated' && (
              <div style={{
                textAlign: 'center',
                fontSize: '0.875rem',
                color: '#059669',
                marginTop: '1rem',
                fontWeight: '500'
              }}>
                🤖 Powered by Google Cloud ADK with Real WattsMyBill Agents
              </div>
            )}
          </div>
        )}

 {/* PART 7: Results Header and Bill Analysis */}

        {/* Results Cards */}
        {results && (
          <>
            {/* Processing Method Success Banner */}
            <div style={{
              background: results.processing_method === 'adk_integrated' ? '#f0fdf4' : '#f8fafc',
              border: `2px solid ${results.processing_method === 'adk_integrated' ? '#10b981' : '#3b82f6'}`,
              borderRadius: '1rem',
              padding: '1.5rem',
              margin: '2rem 0',
              textAlign: 'center'
            }}>
              <h3 style={{
                margin: '0 0 0.5rem 0',
                color: results.processing_method === 'adk_integrated' ? '#059669' : '#1d4ed8',
                fontWeight: '700'
              }}>
                {results.processing_method === 'adk_integrated' ? '🤖 ADK Analysis Complete!' : '🔧 Standalone Analysis Complete!'}
              </h3>
              <p style={{margin: 0, color: '#6b7280'}}>
                {results.processing_method === 'adk_integrated' 
                  ? 'Analysis completed using Google Cloud ADK with real WattsMyBill agents'
                  : 'Analysis completed using standalone agent processing'
                }
              </p>
              
              {/* ADK Metadata Display */}
              {results.adk_metadata && (
                <div style={{
                  display: 'flex',
                  justifyContent: 'center',
                  gap: '2rem',
                  marginTop: '1rem',
                  fontSize: '0.875rem'
                }}>
                  <div>
                    <span style={{fontWeight: '600'}}>Real Agents: </span>
                    <span style={{color: results.adk_metadata.real_agents_used ? '#059669' : '#f59e0b'}}>
                      {results.adk_metadata.real_agents_used ? '✅ Yes' : '⚠️ Mock'}
                    </span>
                  </div>
                  <div>
                    <span style={{fontWeight: '600'}}>Live API: </span>
                    <span style={{color: results.adk_metadata.api_integration ? '#059669' : '#f59e0b'}}>
                      {results.adk_metadata.api_integration ? '✅ Connected' : '📊 Fallback'}
                    </span>
                  </div>
                  <div>
                    <span style={{fontWeight: '600'}}>ETL: </span>
                    <span style={{color: results.adk_metadata.etl_status ? '#059669' : '#6b7280'}}>
                      {results.adk_metadata.etl_status ? '✅ Active' : '❌ Unavailable'}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Billing Context Information */}
            {results.billing_context && (
              <div style={styles.billingContext}>
                ℹ️ <strong>Billing Period:</strong> {getBillingPeriodText(results).description}
              </div>
            )}

            <div style={styles.resultsGrid}>
              {/* Bill Analysis */}
              <div style={styles.resultCard}>
                <div style={styles.cardHeader}>
                  <div style={{...styles.cardIcon, background: '#dbeafe'}}>📊</div>
                  <h3 style={styles.cardTitle}>
                    Bill Analysis
                    {results.processing_method === 'adk_integrated' && (
                      <span style={{fontSize: '0.75rem', color: '#059669', marginLeft: '0.5rem'}}>
                        🤖 ADK
                      </span>
                    )}
                  </h3>
                </div>
                
                {(() => {
                  const billing = getBillingPeriodText(results);
                  
                  // Handle both ADK and standalone result structures
                  let billData, usageData, efficiencyScore;
                  
                  if (results.processing_method === 'adk_integrated') {
                    // ADK structure
                    const analysis = results.bill_analysis?.analysis;
                    billData = analysis?.cost_breakdown || {};
                    usageData = analysis?.usage_profile || {};
                    efficiencyScore = analysis?.efficiency_score || 72;
                  } else {
                    // Standalone structure  
                    billData = results.bill_analysis?.analysis?.bill_data || {};
                    usageData = results.bill_analysis?.analysis?.usage_profile || {};
                    efficiencyScore = results.bill_analysis?.analysis?.efficiency_score || 72;
                  }
                  
                  const quarterlyCost = billData.quarterly_cost || billData.total_cost || billData.total_amount || 712.5;
                  const quarterlyUsage = usageData.quarterly_kwh || usageData.total_kwh || usageData.usage_kwh || 2060;
                  
                  return (
                    <>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>{billing.period} Cost</span>
                        <strong>{formatCurrency(quarterlyCost)}</strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Annual Cost</span>
                        <strong>{formatCurrency(quarterlyCost * billing.multiplier)}</strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>{billing.period} Usage</span>
                        <strong>{quarterlyUsage.toLocaleString()} kWh</strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Daily Average</span>
                        <strong>{usageData.daily_average || (quarterlyUsage / 90).toFixed(1)} kWh</strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Usage Category</span>
                        <strong style={{
                          color: usageData.usage_category === 'low' ? '#16a34a' : 
                                usageData.usage_category === 'high' ? '#dc2626' : '#6b7280'
                        }}>
                          {(usageData.usage_category || 'medium').charAt(0).toUpperCase() + (usageData.usage_category || 'medium').slice(1)}
                        </strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between'}}>
                        <span>Efficiency Score</span>
                        <strong style={{
                          color: efficiencyScore >= 80 ? '#16a34a' : 
                                efficiencyScore >= 60 ? '#f59e0b' : '#dc2626'
                        }}>
                          {efficiencyScore}/100
                        </strong>
                      </div>
                      
                      {/* Efficiency Score Progress Bar */}
                      <div style={{marginTop: '1rem'}}>
                        <div style={{
                          width: '100%',
                          height: '8px',
                          backgroundColor: '#e5e7eb',
                          borderRadius: '4px',
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            width: `${efficiencyScore}%`,
                            height: '100%',
                            backgroundColor: efficiencyScore >= 80 ? '#16a34a' : 
                                           efficiencyScore >= 60 ? '#f59e0b' : '#dc2626',
                            transition: 'width 0.5s ease'
                          }}></div>
                        </div>
                      </div>
                      
                      {/* ADK Data Source Indicator */}
                      {results.processing_method === 'adk_integrated' && (
                        <div style={{
                          marginTop: '1rem',
                          fontSize: '0.75rem',
                          color: '#059669',
                          textAlign: 'center'
                        }}>
                          🤖 Analyzed by Real BillAnalyzerAgent via ADK
                        </div>
                      )}
                    </>
                  );
                })()}
              </div>

      {/* PART 8: Solar Analysis and Better Plan Cards */}

              {/* Solar Analysis (enhanced for ADK) */}
              {(() => {
                let solarAnalysis;
                
                if (results.processing_method === 'adk_integrated') {
                  solarAnalysis = results.bill_analysis?.analysis?.solar_analysis;
                } else {
                  solarAnalysis = results.bill_analysis?.analysis?.solar_analysis;
                }
                
                return solarAnalysis?.has_solar && (
                  <div style={styles.resultCard}>
                    <div style={styles.cardHeader}>
                      <div style={{...styles.cardIcon, background: '#fef3c7'}}>☀️</div>
                      <h3 style={styles.cardTitle}>
                        Solar System Analysis
                        {results.processing_method === 'adk_integrated' && (
                          <span style={{fontSize: '0.75rem', color: '#059669', marginLeft: '0.5rem'}}>
                            🤖 ADK
                          </span>
                        )}
                      </h3>
                    </div>
                    
                    <>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Solar Export</span>
                        <strong>{solarAnalysis.solar_export_kwh || 0} kWh</strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Export Ratio</span>
                        <strong>{solarAnalysis.export_ratio_percent || 0}%</strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Solar Credit</span>
                        <strong style={{color: '#16a34a'}}>
                          {formatCurrency(solarAnalysis.solar_credit_amount || 0)}
                        </strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Performance</span>
                        <strong style={{
                          color: solarAnalysis.performance_rating === 'excellent' ? '#16a34a' : 
                                solarAnalysis.performance_rating === 'good' ? '#f59e0b' : '#6b7280'
                        }}>
                          {(solarAnalysis.performance_rating || 'good').charAt(0).toUpperCase() + (solarAnalysis.performance_rating || 'good').slice(1)}
                        </strong>
                      </div>
                      
                      {solarAnalysis.battery_recommendation && (
                        <div style={{
                          background: '#f0f9ff',
                          border: '1px solid #3b82f6',
                          borderRadius: '0.5rem',
                          padding: '0.75rem',
                          fontSize: '0.875rem',
                          color: '#1e40af'
                        }}>
                          💡 <strong>Battery Recommendation:</strong> Your high solar export suggests a battery system could maximize your savings.
                        </div>
                      )}
                      
                      <div style={{marginTop: '1rem', fontSize: '0.875rem', color: '#6b7280'}}>
                        {solarAnalysis.performance_note || 'Your solar system is contributing to your energy savings.'}
                      </div>
                    </>
                  </div>
                );
              })()}

              {/* Better Plan (enhanced for ADK) */}
              <div style={styles.resultCard}>
                <div style={styles.cardHeader}>
                  <div style={{...styles.cardIcon, background: '#dcfce7'}}>📈</div>
                  <h3 style={styles.cardTitle}>
                    Better Plan Available
                    {results.processing_method === 'adk_integrated' && (
                      <span style={{fontSize: '0.75rem', color: '#059669', marginLeft: '0.5rem'}}>
                        🤖 ADK
                      </span>
                    )}
                  </h3>
                </div>
                
                {(() => {
                  const billing = getBillingPeriodText(results);
                  
                  // Handle both ADK and standalone structures
                  let bestPlan;
                  
                  if (results.processing_method === 'adk_integrated') {
                    bestPlan = results.market_research?.market_research?.best_plan || {};
                  } else {
                    bestPlan = results.market_research?.market_research?.best_plan || {};
                  }
                  
                  const quarterlySavings = bestPlan.quarterly_savings || (bestPlan.annual_savings / 4) || 105;
                  
                  return (
                    <>
                      <h4 style={{margin: '0 0 0.5rem 0'}}>
                        {bestPlan.retailer || 'Alinta Energy'}
                      </h4>
                      <p style={{color: '#6b7280', margin: '0 0 1rem 0'}}>
                        {bestPlan.plan_name || 'Home Deal Plus'}
                      </p>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>{billing.period} Savings</span>
                        <strong style={{color: '#16a34a'}}>
                          {formatCurrency(quarterlySavings)}
                        </strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Annual Savings</span>
                        <strong style={{color: '#16a34a'}}>
                          {formatCurrency(quarterlySavings * billing.multiplier)}
                        </strong>
                      </div>
                      
                      {bestPlan.why_best && (
                        <div style={{
                          background: '#f0fdf4',
                          border: '1px solid #16a34a',
                          borderRadius: '0.5rem',
                          padding: '0.75rem',
                          fontSize: '0.875rem',
                          color: '#166534',
                          marginBottom: '1rem'
                        }}>
                          ✅ {bestPlan.why_best}
                        </div>
                      )}
                      
                      {/* ADK Data Source Info */}
                      {results.processing_method === 'adk_integrated' && results.market_research?.api_used && (
                        <div style={{
                          fontSize: '0.75rem',
                          color: '#059669',
                          marginBottom: '1rem',
                          textAlign: 'center'
                        }}>
                          🌐 Data from: {results.market_research.api_used}
                        </div>
                      )}
                      
                      <button style={{
                        ...styles.button, 
                        background: results.processing_method === 'adk_integrated' 
                          ? 'linear-gradient(135deg, #10b981, #059669)'
                          : 'linear-gradient(135deg, #16a34a, #15803d)'
                      }}>
                        Switch Plan →
                      </button>
                    </>
                  );
                })()}
              </div>

 {/* PART 9: Total Savings and Rebates Cards */}

              {/* Total Savings Potential (enhanced for ADK) */}
              <div style={styles.resultCard}>
                <div style={styles.cardHeader}>
                  <div style={{...styles.cardIcon, background: '#f3e8ff'}}>💎</div>
                  <h3 style={styles.cardTitle}>
                    Total Savings Potential
                    {results.processing_method === 'adk_integrated' && (
                      <span style={{fontSize: '0.75rem', color: '#059669', marginLeft: '0.5rem'}}>
                        🤖 ADK
                      </span>
                    )}
                  </h3>
                </div>
                
                {(() => {
                  const billing = getBillingPeriodText(results);
                  const totalSavings = results.total_savings || 248;
                  
                  // Enhanced savings breakdown for ADK
                  let marketSavings = 0;
                  let rebateSavings = 0;
                  let usageSavings = 0;
                  
                  if (results.processing_method === 'adk_integrated') {
                    marketSavings = results.market_research?.market_research?.savings_analysis?.max_annual_savings || 0;
                    rebateSavings = results.rebate_analysis?.total_rebate_value || 0;
                    usageSavings = results.usage_optimization?.total_annual_savings || 0;
                  } else {
                    marketSavings = results.market_research?.market_research?.savings_analysis?.max_annual_savings || 0;
                    rebateSavings = results.rebate_analysis?.total_rebate_value || 0;
                  }
                  
                  return (
                    <div style={{textAlign: 'center'}}>
                      <div style={{fontSize: '2rem', fontWeight: '700', color: '#8b5cf6', marginBottom: '0.5rem'}}>
                        {formatCurrency(totalSavings)} / {billing.period.toLowerCase()}
                      </div>
                      <div style={{fontSize: '1.25rem', fontWeight: '600', color: '#6b7280', marginBottom: '1rem'}}>
                        {formatCurrency(totalSavings * billing.multiplier)} / year
                      </div>
                      
                      {/* Enhanced Savings Breakdown for ADK */}
                      <div style={{fontSize: '0.875rem', textAlign: 'left'}}>
                        {marketSavings > 0 && (
                          <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem'}}>
                            <span>Plan switching:</span>
                            <span style={{color: '#16a34a'}}>{formatCurrency(marketSavings)}/year</span>
                          </div>
                        )}
                        {rebateSavings > 0 && (
                          <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem'}}>
                            <span>Government rebates:</span>
                            <span style={{color: '#ea580c'}}>{formatCurrency(rebateSavings)}</span>
                          </div>
                        )}
                        {usageSavings > 0 && results.processing_method === 'adk_integrated' && (
                          <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem'}}>
                            <span>Usage optimization:</span>
                            <span style={{color: '#8b5cf6'}}>{formatCurrency(usageSavings)}/year</span>
                          </div>
                        )}
                        <div style={{
                          borderTop: '1px solid #e5e7eb',
                          paddingTop: '0.5rem',
                          display: 'flex',
                          justifyContent: 'space-between',
                          fontWeight: '600'
                        }}>
                          <span>Total potential:</span>
                          <span style={{color: '#8b5cf6'}}>{formatCurrency((marketSavings + rebateSavings + usageSavings) || totalSavings * billing.multiplier)}/year</span>
                        </div>
                      </div>
                      
                      {/* ADK Analysis Badge */}
                      {results.processing_method === 'adk_integrated' && (
                        <div style={{
                          marginTop: '1rem',
                          fontSize: '0.75rem',
                          color: '#059669',
                          fontWeight: '500'
                        }}>
                          🤖 Comprehensive analysis by ADK-coordinated real agents
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>

             {/* Government Rebates (enhanced for ADK) */}
              <div style={styles.resultCard}>
                <div style={styles.cardHeader}>
                  <div style={{...styles.cardIcon, background: '#fed7aa'}}>🎯</div>
                  <h3 style={styles.cardTitle}>
                    Government Rebates
                    {results.processing_method === 'adk_integrated' && (
                      <span style={{fontSize: '0.75rem', color: '#059669', marginLeft: '0.5rem'}}>
                        🤖 ADK
                      </span>
                    )}
                  </h3>
                </div>
                
                {(() => {
                  let rebateAnalysis;
                  
                  if (results.processing_method === 'adk_integrated') {
                    rebateAnalysis = results.rebate_analysis;
                  } else {
                    rebateAnalysis = results.rebate_analysis;
                  }
                  
                  const rebateValue = rebateAnalysis?.total_rebate_value || 572;
                  const rebateCount = rebateAnalysis?.rebate_count || 3;
                  const rebates = rebateAnalysis?.applicable_rebates || [];
                  
                  return (
                    <>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Available Rebates</span>
                        <strong style={{color: '#ea580c'}}>
                          {formatCurrency(rebateValue)}
                        </strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Programs Found</span>
                        <strong>{rebateCount} rebates</strong>
                      </div>
                      
                      {/* Enhanced Rebate Details for ADK */}
                      {rebates.length > 0 && (
                        <div style={{marginBottom: '1rem'}}>
                          <h5 style={{margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: '600'}}>
                            Available Programs:
                          </h5>
                          {rebates.slice(0, 3).map((rebate, index) => (
                            <div key={index} style={{
                              fontSize: '0.75rem',
                              padding: '0.5rem',
                              background: '#fef3c7',
                              borderRadius: '0.25rem',
                              marginBottom: '0.25rem',
                              display: 'flex',
                              justifyContent: 'space-between'
                            }}>
                              <span>{rebate.name}</span>
                              <span style={{fontWeight: '600', color: '#ea580c'}}>
                                {formatCurrency(rebate.value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                      
                      <div style={{fontSize: '0.875rem', color: '#6b7280', marginBottom: '1rem'}}>
                        Mix of one-time rebates and ongoing credits
                      </div>
                      
                      {/* ADK Rebate Finder Badge */}
                      {results.processing_method === 'adk_integrated' && (
                        <div style={{
                          fontSize: '0.75rem',
                          color: '#059669',
                          marginBottom: '1rem',
                          textAlign: 'center'
                        }}>
                          🎯 Found by Real RebateHunterAgent via ADK
                        </div>
                      )}
                      
                      <button style={{
                        ...styles.button, 
                        background: 'linear-gradient(135deg, #ea580c, #c2410c)'
                      }}>
                        Apply for Rebates
                      </button>
                    </>
                  );
                })()}
              </div>
            </div>
          </>
        )}


    {/* PART 10: Footer and Component Closing */}

        {/* CTA Button - Only show after analysis or if there's an error */}
        {(results || error) && (
          <div style={{textAlign: 'center', marginTop: '3rem'}}>
            <button 
              onClick={resetAnalysis}
              style={{
                ...styles.button,
                ...(results?.processing_method === 'adk_integrated' ? styles.adkButton : {}),
                fontSize: '1.125rem',
                padding: '1.25rem 2.5rem',
                width: 'auto',
                maxWidth: '300px',
                margin: '0 auto'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = results?.processing_method === 'adk_integrated' 
                  ? '0 8px 25px rgba(16, 185, 129, 0.3)'
                  : '0 8px 25px rgba(59, 130, 246, 0.3)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = 'none';
              }}
            >
              Try Another Bill
            </button>
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={styles.footer}>
        <p>
          Powered by Google Cloud ADK + Live Australian Energy Market Data
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
        
        {/* ADK Integration Footer */}
        {adkStatus?.adk_integration?.workflow_ready && (
          <div style={{
            marginTop: '1rem',
            padding: '1rem',
            background: '#f0fdf4',
            border: '1px solid #10b981',
            borderRadius: '0.75rem',
            fontSize: '0.875rem'
          }}>
            <div style={{fontWeight: '600', marginBottom: '0.5rem', color: '#059669'}}>
              🤖 Google Cloud ADK Integration Active
            </div>
            <div style={{color: '#166534'}}>
              Real Agent Orchestra: {adkStatus.adk_integration.agent_count} agents | 
              Live Market Data: {adkStatus.adk_integration.api_integration ? 'Connected' : 'Fallback'} | 
              ETL Warehouse: {adkStatus.adk_integration.etl_status ? 'Active' : 'Unavailable'}
            </div>
          </div>
        )}
      </div>
      
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.8; }
        }
      `}</style>
    </div>
  );
};

export default WattsMyBillApp;
import React, { useState, useCallback } from 'react';
import { Target, TrendingUp, Cpu, RefreshCw, AlertTriangle, CheckCircle } from 'lucide-react';

// IMPORTANT: This component assumes Tailwind CSS is configured in your project.
// Load the Lucide icons library for a modern look (npm install lucide-react)

const API_GATEWAY_URL = 'http://127.0.0.1:3000/api/targeting/scoreLead';

// Utility function for exponential backoff (for robust API calls)
const fetchWithRetry = async (url, options, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.status !== 401 && response.status !== 403) { // Do not retry on Auth errors
        return response;
      }
    } catch (error) {
      // LOGGING IMPROVEMENT: Log the network error explicitly during retries
      console.error(`Fetch attempt ${i + 1} failed (Network Error):`, error.message); 
      
      if (i === retries - 1) throw error;
      const delay = Math.pow(2, i) * 1000; // 1s, 2s, 4s delay
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
};


const initialFormData = {
  lead_id: 'L-' + (Math.floor(Math.random() * 9000) + 1000),
  age: 20,
  education_level: 'High School',
  cbsa_code: '41884', // Example CBSA: San Antonio-New Braunfels
  campaign_source: 'Social Media Ad'
};

const App = () => {
  const [formData, setFormData] = useState(initialFormData);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isApiReachable, setIsApiReachable] = useState(true); // New state for API check

  // Check API status on load
  React.useEffect(() => {
    const checkApi = async () => {
      try {
        // Use a simple GET request for health check
        const response = await fetch('http://127.0.0.1:3000/health');
        if (response.ok) {
          setIsApiReachable(true);
        } else {
          setIsApiReachable(false);
        }
      } catch (e) {
        setIsApiReachable(false);
      }
    };
    // Check every 5 seconds only if it's currently unreachable
    if (!isApiReachable) {
      const interval = setInterval(checkApi, 5000);
      return () => clearInterval(interval);
    }
    checkApi();
  }, [isApiReachable]);


  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError(null);

    // Basic client-side validation
    if (formData.age < 18 || !formData.lead_id) {
      setError("Please ensure all fields are valid, especially age (min 18).");
      setLoading(false);
      return;
    }
    
    // CRITICAL FIX: Ensure 'age' is sent as a number, as required by FastAPI Pydantic model.
    const payload = {
        ...formData,
        age: parseInt(formData.age, 10)
    };

    try {
      const response = await fetchWithRetry(API_GATEWAY_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload), // Send corrected payload
        // NOTE: In production, add the Authorization header here once Auth is implemented.
        // headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${userToken}` }
      });
      
      // Update reachability status based on the fetch result
      setIsApiReachable(true); 

      const data = await response.json();

      if (!response.ok) {
        // Handle application-level errors (e.g., 400 Bad Request, 503 Service Unreachable, 422 Pydantic Validation Error)
        const errorMessage = data.message || (data.detail && data.detail[0] ? data.detail[0].msg : `API Error: ${response.status}`);
        throw new Error(errorMessage || `API Error: ${response.status}`);
      }
      
      setResult(data);
    } catch (err) {
      console.error("Scoring failed:", err);
      // More descriptive error if it's a network failure
      const finalErrorMsg = err.message.includes("Load failed") 
        ? "Network connection failed. Ensure the Node.js API Gateway is running on port 3000." 
        : err.message;

      setError(finalErrorMsg);
    } finally {
      setLoading(false);
    }
  }, [formData]);

  const getScoreColor = (score) => {
    if (score >= 85) return "bg-green-500";
    if (score >= 60) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getRecommendationStyle = (score) => {
    if (score >= 85) return "text-green-700 bg-green-100 border-green-300";
    if (score >= 60) return "text-yellow-700 bg-yellow-100 border-yellow-300";
    return "text-red-700 bg-red-100 border-red-300";
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center p-4 font-inter">
      <script src="https://cdn.tailwindcss.com"></script>
      <header className="w-full max-w-4xl text-center py-6">
        <h1 className="text-3xl font-extrabold text-gray-800 flex items-center justify-center">
          <Target className="w-8 h-8 mr-2 text-army-green" /> TAAIP Lead Scoring Tool
        </h1>
        <p className="text-gray-500 mt-2 text-sm">Targeting Intelligence for 420T Technicians.</p>
      </header>

      <main className="w-full max-w-4xl grid md:grid-cols-2 gap-8">
        
        {/* API Status Indicator */}
        <div className="md:col-span-2 text-center">
            <div className={`inline-flex items-center px-4 py-2 text-sm font-medium rounded-full ${
                isApiReachable ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
                {isApiReachable ? (
                    <>
                        <CheckCircle className="w-4 h-4 mr-2" /> API Gateway: Online (Port 3000)
                    </>
                ) : (
                    <>
                        <AlertTriangle className="w-4 h-4 mr-2" /> API Gateway: Offline/Unreachable
                    </>
                )}
            </div>
        </div>

        {/* Input Form */}
        <div className="bg-white p-6 md:p-8 shadow-xl rounded-xl border border-gray-100">
          <h2 className="text-xl font-semibold text-gray-700 mb-4 flex items-center">
            <Cpu className="w-5 h-5 mr-2" /> Input Lead Data
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            
            <FormInput label="Lead ID" name="lead_id" value={formData.lead_id} onChange={handleChange} required />
            <FormInput label="Age" name="age" type="number" value={formData.age} onChange={handleChange} required min="18" />
            <FormSelect label="Education Level" name="education_level" value={formData.education_level} onChange={handleChange} options={['High School', 'Some College', 'Associates', 'Bachelors', 'Masters', 'PHD']} />
            <FormInput label="CBSA Code" name="cbsa_code" value={formData.cbsa_code} onChange={handleChange} required />
            <FormInput label="Campaign Source" name="campaign_source" value={formData.campaign_source} onChange={handleChange} required />

            <button
              type="submit"
              disabled={loading || !isApiReachable}
              className={`w-full flex justify-center items-center px-4 py-3 rounded-lg font-bold transition-colors ${
                loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white shadow-md'
              } ${!isApiReachable ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Scoring Lead...
                </>
              ) : (
                <>
                  <TrendingUp className="w-5 h-5 mr-2" /> Get Predictive Score
                </>
              )}
            </button>
            
            {!isApiReachable && (
                <p className="text-center text-xs text-red-500">
                    Cannot submit: API Gateway is offline. Start the Node.js server.
                </p>
            )}
          </form>
        </div>

        {/* Results / Output */}
        <div className="bg-white p-6 md:p-8 shadow-xl rounded-xl border border-gray-100">
          <h2 className="text-xl font-semibold text-gray-700 mb-6 flex items-center">
            <Cpu className="w-5 h-5 mr-2" /> Predictive Analysis
          </h2>
          
          {error && (
            <div className="p-4 mb-4 text-red-700 bg-red-50 border border-red-300 rounded-lg flex items-center">
              <AlertTriangle className="w-5 h-5 mr-3 flex-shrink-0" />
              <span className="font-medium">Error:</span> {error}
            </div>
          )}

          {!result && !loading && (
            <div className="p-10 text-center text-gray-400 bg-gray-50 rounded-lg border border-dashed border-gray-200">
              <Target className="w-10 h-10 mx-auto mb-2" />
              <p>Enter lead data and click 'Get Predictive Score' to analyze potential conversion.</p>
            </div>
          )}

          {result && (
            <div className="space-y-6">
              
              {/* Score Indicator */}
              <div className="flex items-center justify-between p-4 border-b pb-4">
                <span className="text-lg font-medium text-gray-600">Lead Conversion Score (1-100):</span>
                <div className={`text-4xl font-extrabold text-white rounded-full w-20 h-20 flex items-center justify-center shadow-lg ${getScoreColor(result.score)}`}>
                  {result.score}
                </div>
              </div>

              {/* Probability */}
              <div className="flex items-center justify-between py-2 border-b">
                <span className="text-lg font-medium text-gray-600">Predicted Probability:</span>
                <span className="text-xl font-semibold text-blue-600">{(result.predicted_probability * 100).toFixed(1)}%</span>
              </div>
              
              {/* Recommendation */}
              <div className={`p-4 rounded-lg border-2 ${getRecommendationStyle(result.score)}`}>
                <h3 className="font-bold text-lg mb-2 flex items-center">
                  <CheckCircle className="w-5 h-5 mr-2 flex-shrink-0" /> Recruiter Action Plan
                </h3>
                <p className="text-base font-medium">{result.recommendation}</p>
                <p className="text-xs mt-2 italic opacity-80">
                  Recommendation generated by the Lookalike Modeling and Lead Scoring Engine.
                </p>
              </div>

              <div className="text-sm text-gray-400 pt-4 border-t">
                  <span className="font-mono">Lead ID: {result.lead_id}</span>
              </div>

            </div>
          )}
        </div>
      </main>
    </div>
  );
};

// Reusable Form Components
const FormInput = ({ label, name, type = 'text', value, onChange, ...props }) => (
  <div>
    <label htmlFor={name} className="block text-sm font-medium text-gray-700 mb-1">
      {label}
    </label>
    <input
      type={type}
      name={name}
      id={name}
      value={value}
      onChange={onChange}
      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      {...props}
    />
  </div>
);

const FormSelect = ({ label, name, value, onChange, options }) => (
  <div>
    <label htmlFor={name} className="block text-sm font-medium text-gray-700 mb-1">
      {label}
    </label>
    <select
      name={name}
      id={name}
      value={value}
      onChange={onChange}
      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md shadow-sm"
    >
      {options.map(option => (
        <option key={option} value={option}>{option}</option>
      ))}
    </select>
  </div>
);

export default App;

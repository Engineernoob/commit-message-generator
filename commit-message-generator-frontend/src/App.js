import React, { useState } from 'react';
import Options from './components/Options';
import MessageDisplay from './components/MessageDisplay';
import './App.css';


function App() {
  const [commitMessage, setCommitMessage] = useState('');
  const [error, setError] = useState(null);

  const handleGenerateMessage = async (commitType, customMessage) => {
    setError(null); // Reset error before generating
    try {
      // Use the IPC API to generate a commit message
      const generatedMessage = await window.api.generateCommitMessage(commitType, customMessage);
      setCommitMessage(generatedMessage);
    } catch (err) {
      setError("Failed to generate commit message. Please try again.");
      console.error("Error:", err);
    }
  };

  return (
    <div className="app-container">
      <h1>AI Commit Message Generator</h1>
      <Options onGenerate={handleGenerateMessage} />
      {error && <p className="error">{error}</p>}
      <MessageDisplay message={commitMessage} />
    </div>
  );
}

export default App;

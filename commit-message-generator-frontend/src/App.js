import React, { useState } from 'react';
import Options from './components/Options';
import MessageDisplay from './components/MessageDisplay';

function App() {
  const [commitMessage, setCommitMessage] = useState('');

  const handleGenerateMessage = (message) => {
    setCommitMessage(message);
  };

  return (
    <div>
      <h1>AI Commit Message Generator</h1>
      <Options onGenerate={handleGenerateMessage} />
      <MessageDisplay message={commitMessage} />
    </div>
  );
}

export default App;

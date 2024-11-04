import React, { useState } from 'react';
import { TextField, Button, Typography, Paper, Box, Stack, Card, CardContent } from '@mui/material';

const BACKEND_URL = 'http://127.0.0.1:5000'; // Replace with your backend URL

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [step, setStep] = useState(0);  // To track the user’s step in the process
  const [commitType, setCommitType] = useState(''); // Track commit type

  const handleCommand = async () => {
    if (!input.trim()) return;

    if (step === 0 && input.toLowerCase() === 'generate') {
      setMessages((prevMessages) => [...prevMessages, { type: 'user', text: input }]);
      setMessages((prevMessages) => [...prevMessages, { type: 'system', text: "Choose your class: [feat (Magician), fix (Warrior), chore (Archer)]" }]);
      setStep(1);
    } else if (step === 1) {
      const selectedClass = input.toLowerCase();
      if (['feat', 'fix', 'chore'].includes(selectedClass)) {
        setCommitType(selectedClass);
        setMessages((prevMessages) => [...prevMessages, { type: 'user', text: `Selected Class: ${selectedClass}` }]);
        setMessages((prevMessages) => [...prevMessages, { type: 'system', text: "Enter your commit message:" }]);
        setStep(2);
      } else {
        setMessages((prevMessages) => [...prevMessages, { type: 'error', text: "Invalid class! Choose from [feat, fix, chore]" }]);
      }
    } else if (step === 2) {
      // Send request to Flask backend
      try {
        const res = await fetch(`${BACKEND_URL}/generateCommitMessage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ commitType, customMessage: input }),
        });

        if (res.ok) {
          const data = await res.json();
          const response = `Generated Commit Message: ${data.commitMessage}\nYou gained ${data.experience} experience and slayed ${data.enemiesSlain} enemies.`;
          setMessages((prevMessages) => [...prevMessages, { type: 'system', text: response }]);
        } else {
          setMessages((prevMessages) => [...prevMessages, { type: 'error', text: 'Error generating commit message.' }]);
        }
      } catch (error) {
        setMessages((prevMessages) => [
          ...prevMessages,
          { type: 'error', text: `Error encountered: ${error.message}` },
        ]);
      }
      
      setStep(0);  // Reset the steps for the next command
      setCommitType('');
    }

    setInput('');
  };

  const getMessageColor = (type) => {
    if (type === 'error') return '#ffcccc';
    if (type === 'system') return '#ccffcc';
    return '#cce5ff';
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: 3, backgroundColor: '#1e1e1e', height: '100vh' }}>
      <Typography variant="h4" component="h1" gutterBottom style={{ color: '#ffcc00', fontFamily: 'Courier New' }}>
        Commit Message Quest
      </Typography>

      <Paper
        variant="outlined"
        sx={{
          width: '100%',
          maxWidth: 600,
          height: 400,
          overflowY: 'auto',
          padding: 2,
          marginBottom: 2,
          backgroundColor: '#333',
          borderRadius: 2,
          boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.5)',
        }}
      >
        <Stack spacing={2}>
          {messages.map((msg, index) => (
            <Card
              key={index}
              variant="outlined"
              sx={{
                backgroundColor: getMessageColor(msg.type),
                display: 'flex',
                alignItems: 'center',
                padding: 1,
                borderRadius: 1,
                margin: '5px 0',
              }}
            >
              <CardContent sx={{ padding: 1 }}>
                <Typography sx={{ color: '#333', fontFamily: 'Courier New' }}>{msg.text}</Typography>
              </CardContent>
            </Card>
          ))}
        </Stack>
      </Paper>

      <TextField
        label="Type a command"
        placeholder={step === 0 ? "Type 'generate' to start your quest" : ""}
        variant="outlined"
        fullWidth
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleCommand()}
        sx={{ maxWidth: 600, marginBottom: 2, input: { color: '#e0e0e0' }, backgroundColor: '#444', borderRadius: 1 }}
        InputLabelProps={{
          style: { color: '#e0e0e0' },
        }}
      />
      
      <Button
        variant="contained"
        onClick={handleCommand}
        sx={{ maxWidth: 600, fontSize: '1rem', backgroundColor: '#ffcc00', '&:hover': { backgroundColor: '#ffb300' } }}
      >
        Execute Command
      </Button>
    </Box>
  );
}

export default App;

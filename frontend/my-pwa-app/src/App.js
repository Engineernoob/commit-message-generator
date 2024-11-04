import React, { useState, useEffect } from 'react';
import { TextField, Button, Typography, Paper, Box, Stack, Card, CardContent } from '@mui/material';
import ErrorIcon from '@mui/icons-material/Error';
import PersonIcon from '@mui/icons-material/Person';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

const BACKEND_URL = 'http://localhost:5000';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [step, setStep] = useState(0);
  const [commitType, setCommitType] = useState('');
  const [projectDir, setProjectDir] = useState('/path/to/your/project'); // Update with an actual project path if needed

  useEffect(() => {
    // Display a starting message
    setMessages([{ type: 'system', text: "Welcome to Commit Message Quest! Type 'setup' to configure your project or 'generate' to create a commit message." }]);
  }, []);

  const handleCommand = async () => {
    if (!input.trim()) return;

    setMessages((prevMessages) => [...prevMessages, { type: 'user', text: input }]);

    if (input.toLowerCase() === 'setup' && step === 0) {
      // Call backend for setup
      const res = await fetch(`${BACKEND_URL}/setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ projectDir }),
      });
      const data = await res.json();
      setMessages((prevMessages) => [...prevMessages, { type: 'system', text: data.message }]);
      setStep(1);
    } else if (input.toLowerCase() === 'generate' && step === 1) {
      setMessages((prevMessages) => [...prevMessages, { type: 'system', text: "Choose your class: [feat (Magician), fix (Warrior), chore (Archer)]" }]);
      setStep(2);
    } else if (step === 2) {
      const selectedClass = input.toLowerCase();
      if (['feat', 'fix', 'chore'].includes(selectedClass)) {
        setCommitType(selectedClass);
        setMessages((prevMessages) => [...prevMessages, { type: 'system', text: `Selected Class: ${selectedClass}. Enter your commit message:` }]);
        setStep(3);
      } else {
        setMessages((prevMessages) => [...prevMessages, { type: 'error', text: "Invalid class! Choose from [feat, fix, chore]." }]);
      }
    } else if (step === 3) {
      try {
        const res = await fetch(`${BACKEND_URL}/generateCommitMessage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ projectDir, commitType, customMessage: input }),
        });
        const data = await res.json();
        const response = `Generated Commit Message: ${data.commitMessage}\nYou gained ${data.experience} experience and slayed ${data.enemiesSlain} enemies.`;
        setMessages((prevMessages) => [...prevMessages, { type: 'system', text: response }]);
      } catch (error) {
        setMessages((prevMessages) => [
          ...prevMessages,
          { type: 'error', text: `Error encountered: ${error.message}` },
        ]);
      }
      setStep(0); // Reset steps for the next command
      setCommitType('');
    } else {
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: 'error', text: "Unknown command or incorrect step. Type 'setup' or 'generate' to proceed." },
      ]);
    }

    setInput('');
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
                backgroundColor: msg.type === 'error' ? '#ffcccc' : '#ccffcc',
                display: 'flex',
                alignItems: 'center',
                padding: 1,
                borderRadius: 1,
                margin: '5px 0',
              }}
            >
              <CardContent sx={{ padding: 1, display: 'flex', alignItems: 'center' }}>
                {msg.type === 'error' && <ErrorIcon sx={{ marginRight: 1 }} />}
                {msg.type === 'system' && <CheckCircleIcon sx={{ marginRight: 1 }} />}
                {msg.type === 'user' && <PersonIcon sx={{ marginRight: 1 }} />} {/* Added PersonIcon for user messages */}
                <Typography sx={{ color: '#333', fontFamily: 'Courier New' }}>{msg.text}</Typography>
              </CardContent>
            </Card>
          ))}
        </Stack>
      </Paper>

      <TextField
        label="Type a command"
        placeholder="Type 'setup' or 'generate'"
        variant="outlined"
        fullWidth
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleCommand()}
        sx={{ maxWidth: 600, marginBottom: 2, input: { color: '#e0e0e0' }, backgroundColor: '#444', borderRadius: 1 }}
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


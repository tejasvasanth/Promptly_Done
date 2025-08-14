import React, { useState, useEffect } from 'react';
import axios from 'axios';
import JSZip from 'jszip';
import './animations.css';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Textarea } from './components/ui/textarea';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Alert, AlertDescription } from './components/ui/alert';
import { 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  Download, 
  Copy, 
  Code, 
  Brain,
  Sparkles,
  Wand2,
  Play,
  Eye,
  Palette,
  Star,
  Globe,
  Terminal,
  Monitor,
  FolderOpen,
  Save,
  RotateCcw
} from 'lucide-react';
import './animations.css';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {

  const [initialPrompt, setInitialPrompt] = useState('');
  const [optimizedPrompt, setOptimizedPrompt] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [generatedFiles, setGeneratedFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [selectedFile, setSelectedFile] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [previewMode, setPreviewMode] = useState('code');
  const [animationKey, setAnimationKey] = useState(0);
  const [ideMode, setIdeMode] = useState(false);
  const [fileContent, setFileContent] = useState({});
  const [terminalOutput, setTerminalOutput] = useState('');
  const [terminalInput, setTerminalInput] = useState('');
  const [isTerminalOpen, setIsTerminalOpen] = useState(false);
  
  // Removed authentication states
  
  // Removed project history states
  const [fileTree, setFileTree] = useState([]);
  const [editingFile, setEditingFile] = useState(null);

  // Removed authentication token check

  // Add typing animation effect
  useEffect(() => {
    if (loading) {
      setIsTyping(true);
      const timer = setTimeout(() => setIsTyping(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [loading]);



  const handleOptimizePrompt = async () => {
    if (!initialPrompt.trim()) {
      setError('Please enter a prompt first');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API_BASE_URL}/api/optimize-prompt`, {
        prompt: initialPrompt
      });

      setOptimizedPrompt(response.data.optimized_prompt);
      setSessionId(response.data.session_id);
      setSuccess('Prompt optimized successfully! Review and edit if needed.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to optimize prompt');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateCode = async () => {
    if (!optimizedPrompt.trim()) {
      setError('Please provide an optimized prompt');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API_BASE_URL}/api/generate-code`, {
        optimized_prompt: optimizedPrompt,
        session_id: sessionId
      });

      setGeneratedFiles(response.data.files);
      
      // Initialize file content for editing
      const content = {};
      response.data.files.forEach(file => {
        content[file.path] = file.content;
      });
      setFileContent(content);
      
      // Create file tree structure
      const tree = response.data.files.map(file => ({
        name: file.path.split('/').pop(),
        path: file.path,
        type: 'file',
        content: file.content
      }));
      setFileTree(tree);
      
      setIdeMode(true);
      setSuccess('Code generated successfully! You can now download your files.');
      
      // Removed auto-save functionality
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate code');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadZip = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/download-zip/${sessionId}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'generated_code.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setSuccess('Zip file downloaded successfully!');
    } catch (err) {
      setError('Failed to download zip file');
    }
  };

  const handleDownloadFile = async (fileIndex, fileName) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/download-file/${sessionId}/${fileIndex}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setSuccess(`${fileName} downloaded successfully!`);
    } catch (err) {
      setError(`Failed to download ${fileName}`);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setSuccess('Code copied to clipboard!');
  };

  // File editing functions
  const handleFileEdit = (filePath, newContent) => {
    setFileContent(prev => ({
      ...prev,
      [filePath]: newContent
    }));
    
    // Update the generated files array
    setGeneratedFiles(prev => 
      prev.map(file => 
        file.path === filePath 
          ? { ...file, content: newContent }
          : file
      )
    );
  };

  const handleFileSelect = (filePath) => {
    setEditingFile(filePath);
    setSelectedFile(filePath);
  };

  // Terminal functions
  const handleTerminalCommand = async (command) => {
    setTerminalOutput(prev => prev + `$ ${command}\n`);
    
    // Simulate terminal commands
    if (command.includes('npm start') || command.includes('yarn start')) {
      setTerminalOutput(prev => prev + 'Starting development server...\nServer running on http://localhost:3000\n');
    } else if (command.includes('npm install') || command.includes('yarn install')) {
      setTerminalOutput(prev => prev + 'Installing dependencies...\nDependencies installed successfully!\n');
    } else if (command === 'ls' || command === 'dir') {
      const fileList = fileTree.map(file => file.name).join('  ');
      setTerminalOutput(prev => prev + fileList + '\n');
    } else {
      setTerminalOutput(prev => prev + `Command '${command}' executed\n`);
    }
  };

  const handleTerminalSubmit = (e) => {
    e.preventDefault();
    if (terminalInput.trim()) {
      handleTerminalCommand(terminalInput);
      setTerminalInput('');
    }
  };

  // Live preview function
  const generatePreviewUrl = () => {
    // In a real implementation, this would create a temporary server
    // For now, we'll simulate it
    return 'http://localhost:3001';
  };

  // Removed authentication functions

  // Removed project history functions

  // Removed project history management functions

  const resetFlow = () => {
    setInitialPrompt('');
    setOptimizedPrompt('');
    setSessionId('');
    setGeneratedFiles([]);
    setError('');
    setSuccess('');
    setSelectedFile('');
    setPreviewMode('code');
    setIdeMode(false);
    setFileContent({});
    setFileTree([]);
    setEditingFile(null);
    setTerminalOutput('');
    setTerminalInput('');
    setIsTerminalOpen(false);
    // Removed auth and history reset
  };

  return (
    <div className="min-h-screen bg-black text-green-400 relative overflow-hidden">
      {/* Removed Authentication Modal */}

      {/* Removed Project History Modal */}


      {/* Header */}
      <div className="border-b border-green-500/30 bg-gray-900/80 sticky top-0 z-50 shadow-2xl">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">

              <div>
                <h1 className="text-3xl font-black text-green-400">
                  PromptlyDone
                </h1>
                <p className="text-sm text-white font-medium">✨ AI-powered code generation</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
                <Badge className="bg-green-600 text-black border-0 px-3 py-1 font-medium">
                   <Star className="h-3 w-3 mr-1" />
                   Live Preview
                 </Badge>
              </div>
          </div>
        </div>
      </div>

      {/* Removed Progress Steps */}
      <div className="max-w-7xl mx-auto px-6 py-12 relative z-10">

        {/* Alerts */}
        {error && (
          <Alert className="mb-8 border-red-500/50 bg-red-900/20 backdrop-blur-sm text-red-300 shadow-2xl animate-in slide-in-from-top-5 duration-500">
            <AlertCircle className="h-5 w-5 text-red-400 animate-pulse" />
            <AlertDescription className="text-red-300 font-medium">{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="mb-8 border-green-500/50 bg-green-900/20 backdrop-blur-sm text-green-300 shadow-2xl animate-in slide-in-from-top-5 duration-500">
            <CheckCircle2 className="h-5 w-5 text-green-400 animate-pulse" />
            <AlertDescription className="text-green-300 font-medium">{success}</AlertDescription>
          </Alert>
        )}

        {/* Main Interface */}
        <Card className="max-w-5xl mx-auto shadow-2xl border border-green-500/50 bg-gray-900/80 backdrop-blur-xl animate-in fade-in-50 slide-in-from-bottom-10 duration-700">
          <CardHeader className="text-center pb-8">
            <div className="flex items-center justify-center mb-4">
              <div className="h-16 w-16 bg-green-600 rounded-3xl flex items-center justify-center shadow-2xl animate-pulse">
                <Sparkles className="h-8 w-8 text-black" />
              </div>
            </div>
            <CardTitle className="text-4xl font-black text-green-400 mb-4">
              What would you like to build?
            </CardTitle>
            <CardDescription className="text-xl text-white font-medium leading-relaxed">
              Describe your project in plain English. Our AI will optimize your prompt for better code generation.
            </CardDescription>
          </CardHeader>
            <CardContent className="space-y-8">
              <div className="space-y-6">
                <div className="relative">
                  <Textarea
                    placeholder="Example: Build a todo app with React and FastAPI that allows users to create, edit, delete, and mark tasks as complete. Include user authentication and a clean modern UI..."
                    value={initialPrompt}
                    onChange={(e) => setInitialPrompt(e.target.value)}
                    className="min-h-[180px] resize-none bg-black border border-green-500/50 focus:border-green-400 focus:ring-green-400/20 text-green-400 placeholder-green-600 text-lg backdrop-blur-sm rounded-2xl transition-all duration-300"
                  />
                  {isTyping && (
                    <div className="absolute bottom-4 right-4 flex items-center gap-2 text-green-400">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  )}
                </div>
                <div className="flex flex-wrap gap-3">
                  {[
                    { text: 'Todo App with Authentication', icon: CheckCircle2, color: 'from-green-400 to-emerald-500' },
                    { text: 'REST API with Database', icon: Terminal, color: 'from-blue-400 to-cyan-500' },
                    { text: 'React Dashboard with Charts', icon: Monitor, color: 'from-purple-400 to-pink-500' },
                    { text: 'E-commerce Product Page', icon: Globe, color: 'from-orange-400 to-red-500' },
                    { text: 'Chat Application', icon: Brain, color: 'from-indigo-400 to-purple-500' },
                    { text: 'File Upload System', icon: Globe, color: 'from-teal-400 to-green-500' }
                  ].map((example, index) => (
                    <Badge
                      key={example.text}
                      className={`cursor-pointer bg-gradient-to-r ${example.color} text-white border-0 px-4 py-2 hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-xl animate-in fade-in-50 slide-in-from-bottom-5`}
                      style={{ animationDelay: `${index * 100}ms` }}
                      onClick={() => setInitialPrompt(example.text)}
                    >
                      <example.icon className="h-3 w-3 mr-2" />
                      {example.text}
                    </Badge>
                  ))}
                </div>
              </div>
              <Button
                  onClick={handleOptimizePrompt}
                  disabled={loading || !initialPrompt.trim()}
                  size="lg"
                  className="w-full bg-green-600 hover:bg-green-700 text-black font-bold py-4 text-lg shadow-2xl hover:shadow-green-500/25 transition-all duration-500 transform hover:scale-105 rounded-2xl ripple hover-lift"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-3 h-6 w-6 animate-spin" />
                      <span className="animate-pulse">Optimizing...</span>
                    </>
                  ) : (
                    <>
                      <Wand2 className="mr-3 h-6 w-6 animate-bounce" />
                      Optimize My Prompt
                    </>
                  )}
                </Button>
            </CardContent>
          </Card>
        )}

        {/* Optimized Prompt Section */}
        {optimizedPrompt && (
          <Card className="max-w-6xl mx-auto shadow-2xl border border-green-500/50 bg-gray-900/80 backdrop-blur-xl animate-in fade-in-50 slide-in-from-bottom-10 duration-700">
            <CardHeader>
              <div className="flex items-center justify-center mb-6">
                <div className="h-14 w-14 bg-green-600 rounded-2xl flex items-center justify-center shadow-2xl animate-pulse">
                  <Brain className="h-7 w-7 text-black" />
                </div>
              </div>
              <CardTitle className="text-3xl font-black text-green-400 text-center mb-4">
                Review Optimized Prompt
              </CardTitle>
              <CardDescription className="text-lg text-white text-center font-medium">
                Our AI has enhanced your prompt with technical details. Review and edit if needed.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-8">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="space-y-4">
                  <label className="text-base font-bold text-green-400 mb-3 block flex items-center">
                    <Eye className="h-4 w-4 mr-2" />
                    Original Prompt:
                  </label>
                  <div className="p-6 bg-black/50 backdrop-blur-sm rounded-2xl border border-green-500/30 text-white leading-relaxed shadow-lg">
                    {initialPrompt}
                  </div>
                </div>
                
                <div className="space-y-4">
                  <label className="text-base font-bold text-green-400 mb-3 block flex items-center">
                    <Sparkles className="h-4 w-4 mr-2" />
                    Optimized Prompt:
                  </label>
                  <Textarea
                    value={optimizedPrompt}
                    onChange={(e) => setOptimizedPrompt(e.target.value)}
                    className="min-h-[250px] resize-none bg-black border border-green-500/50 focus:border-green-400 focus:ring-green-400/20 text-green-400 placeholder-green-600 backdrop-blur-sm rounded-2xl transition-all duration-300"
                  />
                </div>
              </div>
              
              <div className="flex gap-4">
                <Button
                  onClick={handleGenerateCode}
                  disabled={loading || !optimizedPrompt.trim()}
                  size="lg"
                  className="flex-1 bg-green-600 hover:bg-green-700 text-black font-bold py-4 text-lg shadow-2xl hover:shadow-green-500/25 transition-all duration-500 transform hover:scale-105 rounded-2xl"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-3 h-6 w-6 animate-spin" />
                      <span className="animate-pulse">Generating Code...</span>
                    </>
                  ) : (
                    <>
                      <Code className="mr-3 h-6 w-6 animate-bounce" />
                      Generate Code
                    </>
                  )}
                </Button>
                <Button
                  onClick={resetFlow}
                  size="lg"
                  className="px-8 bg-gray-800 hover:bg-gray-700 text-green-400 border border-green-500/50 hover:border-green-400 backdrop-blur-sm transition-all duration-300 rounded-2xl"
                >
                  <Brain className="mr-2 h-4 w-4" />
                  Reset
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* IDE Interface */}
        {ideMode && (
          <div className="max-w-full mx-auto h-screen bg-gray-900 text-green-400 flex flex-col animate-in fade-in-50 slide-in-from-bottom-10 duration-700">
            {/* IDE Header */}
            <div className="bg-black border-b border-green-500/50 p-4 flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="h-8 w-8 bg-green-600 rounded-lg flex items-center justify-center">
                  <Code className="h-4 w-4 text-black" />
                </div>
                <h1 className="text-xl font-bold text-green-400">PromptlyDone IDE</h1>
                <Badge className="bg-green-600 text-black border-0">
                  {generatedFiles.length} files generated
                </Badge>
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  onClick={() => setIsTerminalOpen(!isTerminalOpen)}
                  size="sm"
                  className={`px-3 py-1 rounded-lg transition-all duration-300 ${
                    isTerminalOpen
                      ? 'bg-green-600 text-black'
                      : 'bg-gray-800 text-green-400 hover:bg-gray-700 border border-green-500/50'
                  }`}
                >
                  <Terminal className="h-4 w-4 mr-1" />
                  Terminal
                </Button>
                <Button
                  onClick={() => window.open(generatePreviewUrl(), '_blank')}
                  size="sm"
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 text-black rounded-lg transition-all duration-300"
                >
                  <Play className="h-4 w-4 mr-1" />
                  Preview
                </Button>
                <Button
                  onClick={handleDownloadZip}
                  size="sm"
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 text-black rounded-lg transition-all duration-300"
                >
                  <Download className="h-4 w-4 mr-1" />
                  Download
                </Button>

                <Button
                  onClick={resetFlow}
                  size="sm"
                  className="px-3 py-1 bg-gray-800 hover:bg-gray-700 text-green-400 border border-green-500/50 rounded-lg transition-all duration-300"
                >
                  <RotateCcw className="h-4 w-4 mr-1" />
                  New
                </Button>
              </div>
            </div>

            {/* IDE Main Content */}
            <div className="flex flex-1 overflow-hidden">
              {/* File Explorer */}
              <div className="w-64 bg-black border-r border-green-500/50 flex flex-col">
                <div className="p-3 border-b border-green-500/50">
                  <h3 className="text-sm font-semibold text-green-400 uppercase tracking-wide">Explorer</h3>
                </div>
                <div className="flex-1 overflow-y-auto">
                  {fileTree.map((file, index) => (
                    <div
                      key={file.path}
                      onClick={() => handleFileSelect(file.path)}
                      className={`p-3 cursor-pointer hover:bg-gray-800 transition-colors duration-200 border-l-2 ${
                        editingFile === file.path
                          ? 'bg-gray-800 border-green-500 text-green-400'
                          : 'border-transparent text-green-400 hover:text-green-300'
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        <Globe className="h-4 w-4 text-green-400" />
                        <span className="text-sm truncate">{file.name}</span>
                        {index === 0 && <Star className="h-3 w-3 text-green-400" />}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Editor Area */}
              <div className="flex-1 flex flex-col">
                {/* Editor Tabs */}
                {editingFile && (
                  <div className="bg-black border-b border-green-500/50 flex items-center px-4">
                    <div className="flex items-center space-x-2 py-2 px-3 bg-gray-900 rounded-t-lg border-t-2 border-green-500">
                      <Globe className="h-4 w-4 text-green-400" />
                      <span className="text-sm text-green-400">{editingFile.split('/').pop()}</span>
                      <div className="h-2 w-2 bg-green-400 rounded-full"></div>
                    </div>
                  </div>
                )}

                {/* Code Editor */}
                <div className="flex-1 relative">
                  {editingFile ? (
                    <div className="h-full flex flex-col">
                      <div className="flex-1 relative">
                        <Textarea
                          value={fileContent[editingFile] || ''}
                          onChange={(e) => handleFileEdit(editingFile, e.target.value)}
                          className="w-full h-full resize-none bg-black text-green-400 font-mono text-sm border-0 focus:ring-0 p-4 leading-relaxed"
                          placeholder="Start editing your code..."
                        />
                        {/* Line numbers simulation */}
                        <div className="absolute left-0 top-0 w-12 h-full bg-gray-900 border-r border-green-500/50 flex flex-col text-xs text-green-600 pt-4">
                          {(fileContent[editingFile] || '').split('\n').map((_, index) => (
                            <div key={index} className="px-2 leading-relaxed">
                              {index + 1}
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Editor Status Bar */}
                      <div className="bg-black border-t border-green-500/50 px-4 py-2 flex items-center justify-between text-xs text-green-600">
                        <div className="flex items-center space-x-4">
                          <span>Lines: {(fileContent[editingFile] || '').split('\n').length}</span>
                          <span>Characters: {(fileContent[editingFile] || '').length}</span>
                          <span className="flex items-center space-x-1">
                            <div className="h-2 w-2 bg-green-400 rounded-full"></div>
                            <span>Saved</span>
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button
                            onClick={() => copyToClipboard(fileContent[editingFile] || '')}
                            size="sm"
                            className="px-2 py-1 bg-green-600 hover:bg-green-700 text-black text-xs rounded"
                          >
                            <Copy className="h-3 w-3 mr-1" />
                            Copy
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="h-full flex items-center justify-center bg-black">
                      <div className="text-center text-green-600">
                        <Code className="h-16 w-16 mx-auto mb-4" />
                        <p className="text-lg font-medium">Select a file to start editing</p>
                        <p className="text-sm">Choose a file from the explorer to begin coding</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Live Preview Panel */}
              <div className="w-96 bg-black border-l border-green-500/50 flex flex-col">
                <div className="p-3 border-b border-green-500/50 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-green-400">Live Preview</h3>
                  <Button
                    onClick={() => window.open(generatePreviewUrl(), '_blank')}
                    size="sm"
                    className="px-2 py-1 bg-green-600 hover:bg-green-700 text-black text-xs rounded"
                  >
                    <Monitor className="h-3 w-3 mr-1" />
                    Open
                  </Button>
                </div>
                <div className="flex-1 bg-gray-900 m-4 rounded-lg border border-green-500/50 overflow-hidden">
                  <div className="bg-black px-3 py-2 flex items-center space-x-2">
                    <div className="h-3 w-3 bg-red-500 rounded-full"></div>
                    <div className="h-3 w-3 bg-yellow-500 rounded-full"></div>
                    <div className="h-3 w-3 bg-green-500 rounded-full"></div>
                    <div className="flex-1 bg-gray-800 rounded px-2 py-1 text-xs text-green-400">
                      localhost:3001
                    </div>
                  </div>
                  <div className="h-full flex items-center justify-center text-green-600">
                    <div className="text-center">
                      <Monitor className="h-12 w-12 mx-auto mb-2" />
                      <p className="text-sm">Preview will appear here</p>
                      <p className="text-xs">Run your project to see live changes</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Terminal */}
            {isTerminalOpen && (
              <div className="h-64 bg-black border-t border-green-500/50 flex flex-col">
                <div className="bg-black px-4 py-2 flex items-center justify-between border-b border-green-500/50">
                  <div className="flex items-center space-x-2">
                    <Terminal className="h-4 w-4 text-green-400" />
                    <span className="text-sm font-medium text-green-400">Terminal</span>
                  </div>
                  <Button
                    onClick={() => setTerminalOutput('')}
                    size="sm"
                    className="px-2 py-1 bg-gray-800 hover:bg-gray-700 text-green-400 text-xs rounded border border-green-500/50"
                  >
                    Clear
                  </Button>
                </div>
                <div className="flex-1 p-4 overflow-y-auto font-mono text-sm">
                  <pre className="text-green-400 whitespace-pre-wrap">
                    {terminalOutput || 'Welcome to PromptlyDone Terminal\nType your commands below...\n'}
                  </pre>
                </div>
                <form onSubmit={handleTerminalSubmit} className="border-t border-green-500/50 p-4">
                  <div className="flex items-center space-x-2">
                    <span className="text-green-400 font-mono">$</span>
                    <input
                      type="text"
                      value={terminalInput}
                      onChange={(e) => setTerminalInput(e.target.value)}
                      className="flex-1 bg-transparent text-green-400 font-mono text-sm border-0 focus:outline-none"
                      placeholder="Enter command..."
                      autoComplete="off"
                    />
                  </div>
                </form>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
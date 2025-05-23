const { startServer } = require('./whatsapp_bot/server');
const { app: mainApp } = require('./app'); // Ajuste o caminho conforme necessário

async function waitForBotReady() {
    return new Promise((resolve) => {
        const checkStatus = async () => {
            try {
                const response = await fetch('http://localhost:3000/api/status');
                const data = await response.json();
                if (data.isReady) {
                    console.log('✅ Bot do WhatsApp está pronto!');
                    resolve();
                } else {
                    console.log('⏳ Aguardando bot do WhatsApp ficar pronto...');
                    setTimeout(checkStatus, 2000);
                }
            } catch (error) {
                console.log('⏳ Aguardando bot do WhatsApp iniciar...');
                setTimeout(checkStatus, 2000);
            }
        };
        checkStatus();
    });
}

async function startApplication() {
    try {
        console.log('Iniciando aplicação...');
        
        // Iniciar o servidor do bot
        console.log('Iniciando servidor do WhatsApp Bot...');
        await startServer();
        
        // Aguardar o bot ficar pronto
        console.log('Aguardando bot do WhatsApp ficar pronto...');
        await waitForBotReady();
        
        // Iniciar o servidor principal
        const PORT = 3001; // Use uma porta diferente do bot
        mainApp.listen(PORT, () => {
            console.log('==================================================');
            console.log('🚀 APLICAÇÃO PRINCIPAL INICIADA');
            console.log('==================================================');
            console.log(`📡 Servidor principal rodando na porta ${PORT}`);
            console.log('==================================================');
        });
    } catch (error) {
        console.error('Erro ao iniciar aplicação:', error);
        process.exit(1);
    }
}

// Iniciar a aplicação
startApplication(); 
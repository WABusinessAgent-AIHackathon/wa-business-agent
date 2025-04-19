const { createApp } = Vue

createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            messages: [],
            userInput: '',
            isLoading: false,
            quickResources: [
                { text: "What licenses do I need?", action: "requirements" },
                { text: "How much are the fees?", action: "fees" },
                { text: "What's the minimum wage?", action: "wage" },
                { text: "How do I start a business?", action: "steps" },
                { text: "Where can I find more resources?", action: "links" }
            ]
        }
    },
    methods: {
        async sendMessage() {
            if (!this.userInput.trim()) return;

            // Add user message
            this.messages.push({
                text: this.userInput,
                isUser: true
            });

            const userQuestion = this.userInput;
            this.userInput = '';
            this.isLoading = true;

            // Process the message and generate response
            await this.processUserInput(userQuestion);

            this.isLoading = false;
            this.scrollToBottom();
        },

        async processUserInput(input) {
            // Analyze the input and determine the appropriate response
            const lowerInput = input.toLowerCase();
            
            if (lowerInput.includes('license') || lowerInput.includes('permit')) {
                await this.handleLicenseQuery();
            }
            else if (lowerInput.includes('fee') || lowerInput.includes('cost')) {
                await this.handleFeesQuery();
            }
            else if (lowerInput.includes('wage') || lowerInput.includes('salary') || lowerInput.includes('pay')) {
                await this.handleWageQuery();
            }
            else if (lowerInput.includes('start') || lowerInput.includes('begin') || lowerInput.includes('how to')) {
                await this.handleStartingStepsQuery();
            }
            else if (lowerInput.includes('resource') || lowerInput.includes('link') || lowerInput.includes('where')) {
                await this.handleLinksQuery();
            }
            else {
                this.handleGeneralQuery(input);
            }
        },

        async handleLicenseQuery() {
            const response = await fetch('/api/license-requirements');
            const data = await response.json();
            
            this.messages.push({
                text: "Here are the license requirements you need to know:",
                isUser: false,
                data: {
                    type: 'list',
                    content: data.requirements
                },
                actions: [
                    { text: "See related fees", action: "fees" },
                    { text: "How to apply", action: "steps" }
                ]
            });
        },

        async handleFeesQuery() {
            const response = await fetch('/api/fees');
            const data = await response.json();
            
            this.messages.push({
                text: "Here's a breakdown of the business fees:",
                isUser: false,
                data: {
                    type: 'fees',
                    content: data
                },
                actions: [
                    { text: "Start application", action: "steps" },
                    { text: "See requirements", action: "requirements" }
                ]
            });
        },

        async handleWageQuery() {
            const response = await fetch('/api/minimum-wage/washington');
            const data = await response.json();
            
            this.messages.push({
                text: "The current minimum wage in Washington State is:",
                isUser: false,
                data: {
                    type: 'wage',
                    content: data.minimum_wage
                },
                actions: [
                    { text: "Check Seattle rate", action: "wage_seattle" },
                    { text: "Learn more", action: "wage_info" }
                ]
            });
        },

        async handleStartingStepsQuery() {
            const response = await fetch('/api/starting-steps');
            const data = await response.json();
            
            this.messages.push({
                text: "Here's your step-by-step guide to starting a business:",
                isUser: false,
                data: {
                    type: 'steps',
                    content: data.steps
                },
                actions: [
                    { text: "See requirements", action: "requirements" },
                    { text: "Calculate fees", action: "fees" }
                ]
            });
        },

        async handleLinksQuery() {
            const response = await fetch('/api/essential-links');
            const data = await response.json();
            
            this.messages.push({
                text: "Here are some essential resources that might help:",
                isUser: false,
                data: {
                    type: 'links',
                    content: data.links
                }
            });
        },

        handleGeneralQuery(input) {
            this.messages.push({
                text: "I can help you with business licenses, fees, minimum wage information, starting steps, and finding resources. What specific information are you looking for?",
                isUser: false,
                actions: [
                    { text: "License requirements", action: "requirements" },
                    { text: "Business fees", action: "fees" },
                    { text: "Minimum wage", action: "wage" },
                    { text: "Starting steps", action: "steps" },
                    { text: "Resources", action: "links" }
                ]
            });
        },

        async handleQuickAction(action) {
            switch(action.action) {
                case 'requirements':
                    await this.handleLicenseQuery();
                    break;
                case 'fees':
                    await this.handleFeesQuery();
                    break;
                case 'wage':
                    await this.handleWageQuery();
                    break;
                case 'wage_seattle':
                    const response = await fetch('/api/minimum-wage/seattle');
                    const data = await response.json();
                    this.messages.push({
                        text: "The current minimum wage in Seattle is:",
                        isUser: false,
                        data: {
                            type: 'wage',
                            content: data.minimum_wage
                        }
                    });
                    break;
                case 'steps':
                    await this.handleStartingStepsQuery();
                    break;
                case 'links':
                    await this.handleLinksQuery();
                    break;
            }
            this.scrollToBottom();
        },

        formatMessage(text) {
            return text.replace(/\n/g, '<br>');
        },

        formatFeeType(type) {
            return type.split('_').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
        },

        scrollToBottom() {
            setTimeout(() => {
                const container = this.$refs.chatContainer;
                container.scrollTop = container.scrollHeight;
            }, 100);
        }
    },
    mounted() {
        // Initial scroll to bottom
        this.scrollToBottom();
    }
}).mount('#app') 
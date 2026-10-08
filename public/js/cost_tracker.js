/**
 * Client-Side Token Accounting & Financial Cost Tracker.
 * Tracks usage per turn, maintains an audit ledger in localStorage,
 * and enforces budget alert thresholds.
 */

class ClientCostTracker {
  constructor(budgetUsd = 0.50) {
    this.budgetUsd = budgetUsd;
    this.pricingTable = {
      'gpt-4o-mini': { name: 'GPT-4o Mini', promptRate: 0.150, compRate: 0.600 },
      'gpt-4o': { name: 'GPT-4o', promptRate: 2.500, compRate: 10.000 },
      'gemini-1.5-flash': { name: 'Gemini 1.5 Flash', promptRate: 0.075, compRate: 0.300 },
      'gemini-1.5-pro': { name: 'Gemini 1.5 Pro', promptRate: 1.250, compRate: 5.000 },
      'claude-3-5-sonnet': { name: 'Claude 3.5 Sonnet', promptRate: 3.000, compRate: 15.000 },
      'mock-llm': { name: 'Simulation Model', promptRate: 0.0, compRate: 0.0 },
    };
    this.loadState();
  }

  loadState() {
    const raw = localStorage.getItem('nexus_cost_ledger');
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        this.records = parsed.records || [];
        this.budgetUsd = parsed.budgetUsd || this.budgetUsd;
        return;
      } catch (e) {
        console.warn('Failed to parse existing cost ledger');
      }
    }
    this.records = [];
  }

  saveState() {
    localStorage.setItem('nexus_cost_ledger', JSON.stringify({
      records: this.records,
      budgetUsd: this.budgetUsd,
    }));
  }

  estimateTokens(text) {
    if (!text) return 0;
    const chars = text.length;
    const words = text.trim().split(/\s+/).length;
    return Math.max(1, Math.ceil((chars / 4.0 + words * 1.3) / 2.0));
  }

  getRates(model) {
    const clean = (model || 'gpt-4o-mini').toLowerCase();
    for (const [key, val] of Object.entries(this.pricingTable)) {
      if (clean.includes(key)) return val;
    }
    return this.pricingTable['gpt-4o-mini'];
  }

  calculateTurnCost(model, promptTokens, completionTokens) {
    const rates = this.getRates(model);
    const pCost = (promptTokens / 1_000_000.0) * rates.promptRate;
    const cCost = (completionTokens / 1_000_000.0) * rates.compRate;
    return Number((pCost + cCost).toFixed(6));
  }

  recordTurn(model, promptTokens, completionTokens, latencyMs = 0) {
    const cost = this.calculateTurnCost(model, promptTokens, completionTokens);
    const turn = {
      id: this.records.length + 1,
      timestamp: Date.now(),
      model: model,
      promptTokens: promptTokens,
      completionTokens: completionTokens,
      totalTokens: promptTokens + completionTokens,
      costUsd: cost,
      latencyMs: latencyMs,
    };
    this.records.push(turn);
    this.saveState();
    return turn;
  }

  getTotalTokens() {
    return this.records.reduce((acc, r) => acc + r.totalTokens, 0);
  }

  getTotalCost() {
    const sum = this.records.reduce((acc, r) => acc + r.costUsd, 0);
    return Number(sum.toFixed(6));
  }

  getRemainingBudget() {
    return Math.max(0, Number((this.budgetUsd - this.getTotalCost()).toFixed(6)));
  }

  getBudgetUtilizationPercent() {
    if (this.budgetUsd <= 0) return 100;
    return Math.min(100, Number(((this.getTotalCost() / this.budgetUsd) * 100).toFixed(1)));
  }

  isBudgetExceeded() {
    return this.getTotalCost() >= this.budgetUsd;
  }

  resetLedger() {
    this.records = [];
    this.saveState();
  }
}

window.ClientCostTracker = ClientCostTracker;

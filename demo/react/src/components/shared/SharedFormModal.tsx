import React, { useState, useEffect } from 'react';
import { X, Check, AlertCircle, Plus, DollarSign, Wrench, Package } from 'lucide-react';
import {
  Data,
  Vehicle,
  Garage,
  Job,
  Investor,
  Item,
  Batch,
  Sale,
  Expense,
  Payment,
} from '../../types';
import {
  validateRecovery,
  validateCapitalRecovery,
  validateSaleCorrection,
  validateBuyerRefund,
  recoveryLimit,
  fundPosition,
} from '../../utils/selectors';

export type FormModalType =
  | 'vehicle'
  | 'job'
  | 'jobWork'
  | 'jobExpense'
  | 'vehicleExpense'
  | 'customerCharge'
  | 'customerReceipt'
  | 'purchase'
  | 'issue'
  | 'sale'
  | 'collection'
  | 'saleCorrection'
  | 'refund'
  | 'fundCredit'
  | 'investor'
  | 'companyExpense'
  | 'otherIncome'
  | 'recovery'
  | 'capitalRecovery'
  | 'garage'
  | 'garageEdit';

interface SharedFormModalProps {
  isOpen: boolean;
  type: FormModalType | null;
  onClose: () => void;
  data: Data;
  onUpdateData: (updater: (prev: Data) => Data) => void;
  initialContext?: {
    vehicleId?: string;
    jobId?: string;
    saleId?: string;
    investorId?: string;
    garageId?: string;
  };
  onSuccessMessage?: (msg: string) => void;
}

export const SharedFormModal: React.FC<SharedFormModalProps> = ({
  isOpen,
  type,
  onClose,
  data,
  onUpdateData,
  initialContext = {},
  onSuccessMessage,
}) => {
  if (!isOpen || !type) return null;

  const [formData, setFormData] = useState<Record<string, any>>({});
  const [error, setError] = useState<string | null>(null);

  // Initialize defaults based on form type and context
  useEffect(() => {
    setError(null);
    const today = new Date().toISOString().slice(0, 10);
    const defaultGarage = initialContext.garageId || data.garages[0]?.id || 'g-1';

    switch (type) {
      case 'vehicle':
        setFormData({
          type: 'Stock / Investor',
          number: '',
          model: '',
          garageId: defaultGarage,
          person: '',
          investorId: data.investors[0]?.id || '',
          purchase: 0,
        });
        break;
      case 'job':
        setFormData({
          vehicleId: initialContext.vehicleId || data.vehicles[0]?.id || '',
          garageId: defaultGarage,
          description: '',
          date: today,
        });
        break;
      case 'jobWork':
        setFormData({
          jobId: initialContext.jobId || data.jobs[0]?.id || '',
          category: 'Work',
          description: '',
          date: today,
        });
        break;
      case 'jobExpense':
        setFormData({
          jobId: initialContext.jobId || data.jobs[0]?.id || '',
          vehicleId: initialContext.vehicleId || data.vehicles[0]?.id || '',
          description: '',
          costType: 'Labour',
          date: today,
          amount: 0,
          investor: 0,
          capital: 0,
        });
        break;
      case 'vehicleExpense':
        setFormData({
          vehicleId: initialContext.vehicleId || data.vehicles[0]?.id || '',
          garageId: defaultGarage,
          description: '',
          costType: 'Other',
          date: today,
          amount: 0,
          investor: 0,
          capital: 0,
        });
        break;
      case 'customerCharge':
        setFormData({
          jobId: initialContext.jobId || data.jobs[0]?.id || '',
          category: 'Work',
          description: '',
          amount: 0,
          date: today,
        });
        break;
      case 'customerReceipt':
        setFormData({
          jobId: initialContext.jobId || data.jobs[0]?.id || '',
          amount: 0,
          method: 'Bank transfer',
          date: today,
        });
        break;
      case 'purchase':
        setFormData({
          itemId: data.items[0]?.id || '',
          newItemName: '',
          category: 'General',
          garageId: defaultGarage,
          quantity: 1,
          cost: 0,
          date: today,
        });
        break;
      case 'issue':
        setFormData({
          batchId: data.batches[0]?.id || '',
          vehicleId: initialContext.vehicleId || data.vehicles[0]?.id || '',
          jobId: initialContext.jobId || data.jobs[0]?.id || '',
          quantity: 1,
          price: 0,
          investor: 0,
          capital: 0,
          date: today,
        });
        break;
      case 'sale':
        setFormData({
          vehicleId: initialContext.vehicleId || data.vehicles.find((v) => v.status !== 'Sold')?.id || '',
          buyer: '',
          price: 0,
        });
        break;
      case 'collection':
        setFormData({
          saleId: initialContext.saleId || data.sales[0]?.id || '',
          amount: 0,
          method: 'Bank transfer',
          date: today,
        });
        break;
      case 'saleCorrection':
        setFormData({
          saleId: initialContext.saleId || data.sales[0]?.id || '',
          price: 0,
          reason: '',
          date: today,
        });
        break;
      case 'refund':
        setFormData({
          saleId: initialContext.saleId || data.sales[0]?.id || '',
          amount: 0,
          method: 'Bank transfer',
          reason: '',
          date: today,
        });
        break;
      case 'fundCredit':
        setFormData({
          investorId: initialContext.investorId || data.investors[0]?.id || '',
          amount: 0,
          note: 'Additional working capital contribution',
          date: today,
        });
        break;
      case 'investor':
        setFormData({
          name: '',
          principal: 0,
        });
        break;
      case 'companyExpense':
        setFormData({
          garageId: defaultGarage,
          description: '',
          costType: 'Other',
          date: today,
          amount: 0,
        });
        break;
      case 'otherIncome':
        setFormData({
          garageId: defaultGarage,
          source: '',
          description: '',
          amount: 0,
          method: 'Bank transfer',
        });
        break;
      case 'recovery':
        setFormData({
          vehicleId: initialContext.vehicleId || data.vehicles[0]?.id || '',
          amount: 0,
          date: today,
        });
        break;
      case 'capitalRecovery':
        setFormData({
          vehicleId: initialContext.vehicleId || data.vehicles[0]?.id || '',
          amount: 0,
          method: 'Bank transfer',
          date: today,
        });
        break;
      case 'garage':
        setFormData({
          name: '',
          location: '',
        });
        break;
      case 'garageEdit':
        const g = data.garages.find((x) => x.id === initialContext.garageId) || data.garages[0];
        setFormData({
          garageId: g?.id || '',
          name: g?.name || '',
          location: g?.location || '',
        });
        break;
      default:
        setFormData({});
    }
  }, [type, initialContext, isOpen]);

  const handleChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      switch (type) {
        case 'vehicle': {
          if (!formData.number.trim() || !formData.model.trim()) {
            throw new Error('Vehicle registration number and model are required.');
          }
          const newVeh: Vehicle = {
            id: 'v-' + Date.now(),
            number: formData.number.trim().toUpperCase(),
            model: formData.model.trim(),
            type: formData.type,
            garageId: formData.garageId,
            person: formData.person.trim() || 'Direct Owner',
            investorId: formData.type === 'Stock / Investor' ? formData.investorId : undefined,
            status: formData.type === 'Customer' ? 'Customer Vehicle' : 'Purchased',
            purchase: Number(formData.purchase) || 0,
            totalCost: Number(formData.purchase) || 0,
          };
          onUpdateData((prev) => ({
            ...prev,
            vehicles: [newVeh, ...prev.vehicles],
            audit: [
              {
                id: 'aud-' + Date.now(),
                date: new Date().toISOString().slice(0, 10),
                action: 'Vehicle registered',
                detail: `${newVeh.number} · ${newVeh.model}`,
              },
              ...prev.audit,
            ],
          }));
          onSuccessMessage?.(`Vehicle ${newVeh.number} registered successfully.`);
          break;
        }

        case 'job': {
          if (!formData.description.trim()) {
            throw new Error('Please enter a description for the job.');
          }
          const jobNum = 'JOB-' + (1040 + data.jobs.length + 1);
          const newJob: Job = {
            id: 'j-' + Date.now(),
            vehicleId: formData.vehicleId,
            garageId: formData.garageId,
            number: jobNum,
            description: formData.description.trim(),
            status: 'Open',
            date: formData.date,
            charge: 0,
            received: 0,
            workEntries: [],
            costs: [],
            charges: [],
            statusHistory: [
              {
                id: 'sh-' + Date.now(),
                timestamp: new Date().toISOString().slice(0, 16).replace('T', ' '),
                from: 'Draft',
                to: 'Open',
                actor: 'Technician',
                note: 'Job initiated',
              },
            ],
          };
          onUpdateData((prev) => ({
            ...prev,
            jobs: [newJob, ...prev.jobs],
            audit: [
              {
                id: 'aud-' + Date.now(),
                date: formData.date,
                action: 'Garage Job Created',
                detail: `${jobNum} · ${newJob.description}`,
              },
              ...prev.audit,
            ],
          }));
          onSuccessMessage?.(`Garage Job ${jobNum} created.`);
          break;
        }

        case 'customerReceipt': {
          const amt = Number(formData.amount);
          if (amt <= 0) throw new Error('Receipt amount must be greater than zero.');
          const targetJob = data.jobs.find((j) => j.id === formData.jobId);
          if (!targetJob) throw new Error('Selected job not found.');

          const newPayment: Payment = {
            id: 'pay-' + Date.now(),
            kind: 'customer',
            targetId: targetJob.id,
            amount: amt,
            date: formData.date,
            method: formData.method,
          };

          // Finding R-01 Resolution: Appends to data.payments AND updates job.received
          onUpdateData((prev) => ({
            ...prev,
            payments: [newPayment, ...prev.payments],
            jobs: prev.jobs.map((j) =>
              j.id === targetJob.id ? { ...j, received: j.received + amt } : j
            ),
            audit: [
              {
                id: 'aud-' + Date.now(),
                date: formData.date,
                action: 'Customer receipt recorded',
                detail: `${targetJob.number} · ₹${amt.toLocaleString('en-IN')} via ${formData.method}`,
              },
              ...prev.audit,
            ],
          }));
          onSuccessMessage?.(`Receipt of ₹${amt.toLocaleString('en-IN')} recorded for ${targetJob.number}.`);
          break;
        }

        case 'collection': {
          const amt = Number(formData.amount);
          if (amt <= 0) throw new Error('Collection amount must be greater than zero.');
          const targetSale = data.sales.find((s) => s.id === formData.saleId);
          if (!targetSale) throw new Error('Selected sale not found.');

          const newPayment: Payment = {
            id: 'pay-' + Date.now(),
            kind: 'buyer',
            targetId: targetSale.id,
            amount: amt,
            date: formData.date,
            method: formData.method,
          };

          onUpdateData((prev) => ({
            ...prev,
            payments: [newPayment, ...prev.payments],
            sales: prev.sales.map((s) =>
              s.id === targetSale.id ? { ...s, received: s.received + amt } : s
            ),
            audit: [
              {
                id: 'aud-' + Date.now(),
                date: formData.date,
                action: 'Buyer collection recorded',
                detail: `Sale ${targetSale.buyer} · ₹${amt.toLocaleString('en-IN')} via ${formData.method}`,
              },
              ...prev.audit,
            ],
          }));
          onSuccessMessage?.(`Collection of ₹${amt.toLocaleString('en-IN')} recorded.`);
          break;
        }

        case 'purchase': {
          const qty = Number(formData.quantity);
          const cost = Number(formData.cost);
          if (qty <= 0 || cost <= 0) throw new Error('Quantity and cost must be positive.');

          let itemId = formData.itemId;
          let newItems = [...data.items];
          if (formData.newItemName?.trim()) {
            const newItem: Item = {
              id: 'it-' + Date.now(),
              name: formData.newItemName.trim(),
              category: formData.category || 'General',
              active: true,
            };
            newItems.push(newItem);
            itemId = newItem.id;
          }

          const newBatch: Batch = {
            id: 'b-' + Date.now(),
            itemId,
            garageId: formData.garageId,
            date: formData.date,
            quantity: qty,
            cost,
          };

          onUpdateData((prev) => ({
            ...prev,
            items: newItems,
            batches: [newBatch, ...prev.batches],
            audit: [
              {
                id: 'aud-' + Date.now(),
                date: formData.date,
                action: 'Inventory purchase recorded',
                detail: `Batch ${newBatch.id.slice(-6)} · ${qty} units @ ₹${cost}`,
              },
              ...prev.audit,
            ],
          }));
          onSuccessMessage?.(`Purchased ${qty} units of inventory.`);
          break;
        }

        case 'companyExpense': {
          const amt = Number(formData.amount);
          if (amt <= 0) throw new Error('Amount must be positive.');
          if (!formData.description.trim()) throw new Error('Description is required.');

          const newExp: Expense = {
            id: 'exp-' + Date.now(),
            vehicleId: '',
            garageId: formData.garageId,
            description: formData.description.trim(),
            amount: amt,
            investor: 0,
            capital: 0,
            date: formData.date,
            category: 'Company',
            costType: formData.costType,
          };

          onUpdateData((prev) => ({
            ...prev,
            expenses: [newExp, ...prev.expenses],
            audit: [
              {
                id: 'aud-' + Date.now(),
                date: formData.date,
                action: 'Company expense recorded',
                detail: `${newExp.description} · ₹${amt.toLocaleString('en-IN')}`,
              },
              ...prev.audit,
            ],
          }));
          onSuccessMessage?.(`Company expense of ₹${amt.toLocaleString('en-IN')} logged.`);
          break;
        }

        case 'otherIncome': {
          const amt = Number(formData.amount);
          if (amt <= 0) throw new Error('Amount must be positive.');
          if (!formData.description.trim()) throw new Error('Description is required.');

          const newReceipt = {
            id: 'inc-' + Date.now(),
            garageId: formData.garageId,
            source: formData.source.trim() || 'Operational',
            description: formData.description.trim(),
            amount: amt,
            method: formData.method,
            timestamp: new Date().toISOString().slice(0, 16).replace('T', ' '),
            actor: 'Accountant',
          };

          onUpdateData((prev) => ({
            ...prev,
            otherIncomeReceipts: [newReceipt, ...(prev.otherIncomeReceipts ?? [])],
            audit: [
              {
                id: 'aud-' + Date.now(),
                date: new Date().toISOString().slice(0, 10),
                action: 'Other operational income recorded',
                detail: `${newReceipt.description} · ₹${amt.toLocaleString('en-IN')} from ${newReceipt.source}`,
              },
              ...prev.audit,
            ],
          }));
          onSuccessMessage?.(`Recorded other income of ₹${amt.toLocaleString('en-IN')}.`);
          break;
        }

        case 'recovery': {
          const amt = Number(formData.amount);
          validateRecovery(data, formData.vehicleId, amt);
          const limitRes = recoveryLimit(data, formData.vehicleId);

          const newRec = {
            id: 'rec-' + Date.now(),
            vehicleId: formData.vehicleId,
            saleId: limitRes.saleId,
            amount: amt,
            date: formData.date,
          };

          onUpdateData((prev) => ({
            ...prev,
            principalRecoveries: [newRec, ...(prev.principalRecoveries ?? [])],
            audit: [
              {
                id: 'aud-' + Date.now(),
                date: formData.date,
                action: 'Principal recovery recorded',
                detail: `Vehicle ${formData.vehicleId} · ₹${amt.toLocaleString('en-IN')} recovered`,
              },
              ...prev.audit,
            ],
          }));
          onSuccessMessage?.(`Principal recovery of ₹${amt.toLocaleString('en-IN')} recorded.`);
          break;
        }

        case 'capitalRecovery': {
          const amt = Number(formData.amount);
          const valRes = validateCapitalRecovery(data, formData.vehicleId, amt);

          const newPayment: Payment = {
            id: 'pay-' + Date.now(),
            kind: 'capital',
            targetId: formData.vehicleId,
            amount: amt,
            date: formData.date,
            method: formData.method,
          };

          onUpdateData((prev) => ({
            ...prev,
            payments: [newPayment, ...prev.payments],
            audit: [
              {
                id: 'aud-' + Date.now(),
                date: formData.date,
                action: 'Capital recovery recorded',
                detail: `Vehicle ${formData.vehicleId} · ₹${amt.toLocaleString('en-IN')} returned to company`,
              },
              ...prev.audit,
            ],
          }));
          onSuccessMessage?.(`Capital recovery of ₹${amt.toLocaleString('en-IN')} confirmed.`);
          break;
        }

        case 'saleCorrection': {
          const newPrice = Number(formData.price);
          validateSaleCorrection(data, formData.saleId, newPrice, formData.reason);

          onUpdateData((prev) => ({
            ...prev,
            sales: prev.sales.map((s) =>
              s.id === formData.saleId
                ? {
                    ...s,
                    corrections: [
                      ...(s.corrections ?? []),
                      {
                        id: 'sc-' + Date.now(),
                        date: formData.date,
                        actor: 'Accountant',
                        reason: formData.reason,
                        oldPrice: s.price,
                        price: newPrice,
                      },
                    ],
                  }
                : s
            ),
            audit: [
              {
                id: 'aud-' + Date.now(),
                date: formData.date,
                action: 'Sale price corrected',
                detail: `Sale ${formData.saleId} adjusted to ₹${newPrice.toLocaleString('en-IN')}: ${formData.reason}`,
              },
              ...prev.audit,
            ],
          }));
          onSuccessMessage?.(`Sale price corrected to ₹${newPrice.toLocaleString('en-IN')}.`);
          break;
        }

        case 'refund': {
          const amt = Number(formData.amount);
          const refundRes = validateBuyerRefund(data, formData.saleId, amt);

          const newRefund = {
            id: 'ref-' + Date.now(),
            saleId: formData.saleId,
            amount: amt,
            principalBacked: refundRes.principalBacked,
            date: formData.date,
            method: formData.method,
            reason: formData.reason,
          };

          onUpdateData((prev) => ({
            ...prev,
            buyerRefunds: [newRefund, ...(prev.buyerRefunds ?? [])],
            audit: [
              {
                id: 'aud-' + Date.now(),
                date: formData.date,
                action: 'Buyer refund executed',
                detail: `Sale ${formData.saleId} · ₹${amt.toLocaleString('en-IN')} refunded (${formData.reason})`,
              },
              ...prev.audit,
            ],
          }));
          onSuccessMessage?.(`Buyer refund of ₹${amt.toLocaleString('en-IN')} logged.`);
          break;
        }

        default: {
          onSuccessMessage?.(`Action completed.`);
          break;
        }
      }

      onClose();
    } catch (err: any) {
      setError(err?.message || 'Operation failed. Please verify inputs.');
    }
  };

  // Human-readable modal titles
  const getModalTitle = () => {
    switch (type) {
      case 'vehicle':
        return 'Register New Vehicle';
      case 'job':
        return 'Create Garage Work Order';
      case 'jobWork':
        return 'Add Work Log Entry';
      case 'jobExpense':
        return 'Record Job Expense';
      case 'vehicleExpense':
        return 'Record Vehicle Expense';
      case 'customerCharge':
        return 'Add Customer Charge';
      case 'customerReceipt':
        return 'Record Customer Payment Receipt';
      case 'purchase':
        return 'Receive Inventory Purchase Batch';
      case 'issue':
        return 'Issue Stock to Work Order / Vehicle';
      case 'sale':
        return 'Contract Vehicle Sale';
      case 'collection':
        return 'Record Buyer Collection';
      case 'saleCorrection':
        return 'Correct Vehicle Sale Price';
      case 'refund':
        return 'Process Buyer Refund';
      case 'fundCredit':
        return 'Add Investor Capital Credit';
      case 'investor':
        return 'Register New Investor';
      case 'companyExpense':
        return 'Record Workshop Overhead Expense';
      case 'otherIncome':
        return 'Record Other Operational Income';
      case 'recovery':
        return 'Confirm Investor Principal Recovery';
      case 'capitalRecovery':
        return 'Record Company Running Capital Recovery';
      case 'garage':
        return 'Add Garage Branch';
      case 'garageEdit':
        return 'Edit Garage Branch Details';
      default:
        return 'Form Dialog';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-100">
      <div className="bg-white dark:bg-zinc-900 border border-[#e2d8ce] dark:border-zinc-800 rounded-[24px] shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#f0e7df] dark:border-zinc-800 flex items-center justify-between">
          <div>
            <h3 className="text-base font-extrabold text-gray-950 dark:text-white">
              {getModalTitle()}
            </h3>
            <p className="text-[11px] text-gray-500 dark:text-gray-400">
              VIRMS Operational Dialog · Live State Sync
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 flex items-center justify-center text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/50 flex items-start gap-2.5 text-xs text-red-700 dark:text-red-300 font-medium">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-600" />
              <span>{error}</span>
            </div>
          )}

          {/* Form Fields according to type */}
          {type === 'vehicle' && (
            <>
              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Classification
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {['Stock / Investor', 'Customer'].map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => handleChange('type', t)}
                      className={`px-3 py-2 rounded-xl text-xs font-bold border transition ${
                        formData.type === t
                          ? 'bg-[#18181b] text-white border-[#18181b]'
                          : 'bg-white dark:bg-zinc-800 border-[#e2d8ce] dark:border-zinc-700 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Registration Number
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. KL 11 AB 4821"
                  value={formData.number || ''}
                  onChange={(e) => handleChange('number', e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Model & Description
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Jeep Wrangler Rubicon 2.0L"
                  value={formData.model || ''}
                  onChange={(e) => handleChange('model', e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                    Garage Location
                  </label>
                  <select
                    value={formData.garageId || ''}
                    onChange={(e) => handleChange('garageId', e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                  >
                    {data.garages.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                    {formData.type === 'Customer' ? 'Customer Name' : 'Associated Investor'}
                  </label>
                  {formData.type === 'Customer' ? (
                    <input
                      type="text"
                      placeholder="Customer name"
                      value={formData.person || ''}
                      onChange={(e) => handleChange('person', e.target.value)}
                      className="w-full px-3 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                    />
                  ) : (
                    <select
                      value={formData.investorId || ''}
                      onChange={(e) => handleChange('investorId', e.target.value)}
                      className="w-full px-3 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                    >
                      {data.investors.map((i) => (
                        <option key={i.id} value={i.id}>
                          {i.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              </div>

              {formData.type === 'Stock / Investor' && (
                <div>
                  <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                    Purchase Price (₹)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="1000"
                    value={formData.purchase || 0}
                    onChange={(e) => handleChange('purchase', e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-sm font-semibold"
                  />
                </div>
              )}
            </>
          )}

          {type === 'customerReceipt' && (
            <>
              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Select Work Order / Job
                </label>
                <select
                  value={formData.jobId || ''}
                  onChange={(e) => handleChange('jobId', e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                >
                  {data.jobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.number} · {j.description} (Charge: ₹{j.charge}, Paid: ₹{j.received})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                    Receipt Amount (₹)
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={formData.amount || ''}
                    onChange={(e) => handleChange('amount', e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-sm font-semibold"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                    Payment Method
                  </label>
                  <select
                    value={formData.method || 'Bank transfer'}
                    onChange={(e) => handleChange('method', e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                  >
                    <option value="Bank transfer">Bank transfer</option>
                    <option value="UPI">UPI</option>
                    <option value="Cash">Cash</option>
                    <option value="Cheque">Cheque</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Payment Date
                </label>
                <input
                  type="date"
                  value={formData.date || ''}
                  onChange={(e) => handleChange('date', e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                />
              </div>
            </>
          )}

          {type === 'collection' && (
            <>
              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Select Vehicle Sale
                </label>
                <select
                  value={formData.saleId || ''}
                  onChange={(e) => handleChange('saleId', e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                >
                  {data.sales.map((s) => (
                    <option key={s.id} value={s.id}>
                      Buyer: {s.buyer} · Price: ₹{s.price} (Collected: ₹{s.received})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                    Amount Collected (₹)
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={formData.amount || ''}
                    onChange={(e) => handleChange('amount', e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-sm font-semibold"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                    Payment Method
                  </label>
                  <select
                    value={formData.method || 'Bank transfer'}
                    onChange={(e) => handleChange('method', e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                  >
                    <option value="Bank transfer">Bank transfer</option>
                    <option value="UPI">UPI</option>
                    <option value="Cash">Cash</option>
                  </select>
                </div>
              </div>
            </>
          )}

          {type === 'job' && (
            <>
              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Select Vehicle
                </label>
                <select
                  value={formData.vehicleId || ''}
                  onChange={(e) => handleChange('vehicleId', e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                >
                  {data.vehicles.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.number} · {v.model} ({v.type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Garage Branch
                </label>
                <select
                  value={formData.garageId || ''}
                  onChange={(e) => handleChange('garageId', e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                >
                  {data.garages.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Job Description / Work Scope
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="e.g. Full mechanical inspection & transmission rebuild"
                  value={formData.description || ''}
                  onChange={(e) => handleChange('description', e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                />
              </div>
            </>
          )}

          {type === 'companyExpense' && (
            <>
              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Workshop Branch
                </label>
                <select
                  value={formData.garageId || ''}
                  onChange={(e) => handleChange('garageId', e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                >
                  {data.garages.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Expense Description
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Hydraulic lift monthly maintenance"
                  value={formData.description || ''}
                  onChange={(e) => handleChange('description', e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                    Amount (₹)
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={formData.amount || ''}
                    onChange={(e) => handleChange('amount', e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-sm font-semibold"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                    Expense Date
                  </label>
                  <input
                    type="date"
                    value={formData.date || ''}
                    onChange={(e) => handleChange('date', e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                  />
                </div>
              </div>
            </>
          )}

          {type === 'otherIncome' && (
            <>
              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Garage Branch
                </label>
                <select
                  value={formData.garageId || ''}
                  onChange={(e) => handleChange('garageId', e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                >
                  {data.garages.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Source / Payer
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Scrap Metals Corp, Battery recycling"
                  value={formData.source || ''}
                  onChange={(e) => handleChange('source', e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Receipt Description
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Workshop scrap metal & tire recycling payout"
                  value={formData.description || ''}
                  onChange={(e) => handleChange('description', e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                    Amount (₹)
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={formData.amount || ''}
                    onChange={(e) => handleChange('amount', e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-sm font-semibold"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                    Method
                  </label>
                  <select
                    value={formData.method || 'Bank transfer'}
                    onChange={(e) => handleChange('method', e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                  >
                    <option value="Bank transfer">Bank transfer</option>
                    <option value="UPI">UPI</option>
                    <option value="Cash">Cash</option>
                  </select>
                </div>
              </div>
            </>
          )}

          {type === 'recovery' && (
            <>
              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Select Funded Vehicle
                </label>
                <select
                  value={formData.vehicleId || ''}
                  onChange={(e) => handleChange('vehicleId', e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                >
                  {data.vehicles
                    .filter((v) => v.type === 'Stock / Investor' && v.investorId)
                    .map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.number} · {v.model} (Investor: {v.person})
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Recovery Amount (₹)
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  value={formData.amount || ''}
                  onChange={(e) => handleChange('amount', e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-sm font-semibold"
                />
              </div>
            </>
          )}

          {type === 'capitalRecovery' && (
            <>
              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Select Stock Vehicle
                </label>
                <select
                  value={formData.vehicleId || ''}
                  onChange={(e) => handleChange('vehicleId', e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                >
                  {data.vehicles
                    .filter((v) => v.type === 'Stock / Investor')
                    .map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.number} · {v.model}
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Company Capital Recovery (₹)
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  value={formData.amount || ''}
                  onChange={(e) => handleChange('amount', e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-sm font-semibold"
                />
              </div>
            </>
          )}

          {/* Fallback general form if not custom-rendered */}
          {!['vehicle', 'customerReceipt', 'collection', 'job', 'companyExpense', 'otherIncome', 'recovery', 'capitalRecovery'].includes(type) && (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Primary Amount / Value (₹)
                </label>
                <input
                  type="number"
                  required
                  value={formData.amount ?? formData.price ?? 0}
                  onChange={(e) => {
                    const val = e.target.value;
                    handleChange('amount', val);
                    handleChange('price', val);
                  }}
                  className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-sm font-semibold"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Reason / Description
                </label>
                <input
                  type="text"
                  required
                  placeholder="Operational reason / note"
                  value={formData.description ?? formData.reason ?? formData.note ?? ''}
                  onChange={(e) => {
                    const val = e.target.value;
                    handleChange('description', val);
                    handleChange('reason', val);
                    handleChange('note', val);
                  }}
                  className="w-full px-3.5 py-2 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-semibold"
                />
              </div>
            </div>
          )}

          {/* Form Actions */}
          <div className="pt-4 border-t border-[#f0e7df] dark:border-zinc-800 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-full border border-[#e2d8ce] dark:border-zinc-700 hover:bg-gray-100 dark:hover:bg-zinc-800 text-xs font-bold text-gray-700 dark:text-gray-300 transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-full bg-[#18181b] hover:bg-black text-white text-xs font-bold shadow-xs transition cursor-pointer flex items-center gap-1.5 active:scale-95"
            >
              <Check className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
              <span>Confirm & Record</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

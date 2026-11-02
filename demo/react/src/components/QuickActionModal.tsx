import React, { useState } from 'react';
import { X, Check } from 'lucide-react';
import { Garage, Investor } from '../types';

interface QuickActionModalProps {
  isOpen: boolean;
  type: 'receipt' | 'sale' | 'vehicle' | null;
  onClose: () => void;
  garages: Garage[];
  investors: Investor[];
  onSubmitSuccess: (message: string, createdItem?: any) => void;
}

export const QuickActionModal: React.FC<QuickActionModalProps> = ({
  isOpen,
  type,
  onClose,
  garages,
  investors,
  onSubmitSuccess,
}) => {
  const [buyerName, setBuyerName] = useState('Rohan Das');
  const [amount, setAmount] = useState('50000');
  const [paymentMethod, setPaymentMethod] = useState('Bank transfer');
  const [vehicleReg, setVehicleReg] = useState('KL 11 AB 4821');
  const [vehicleModel, setVehicleModel] = useState('Jeep Compass Longitude');
  const [salePrice, setSalePrice] = useState('650000');
  const [selectedInvestor, setSelectedInvestor] = useState(investors[0]?.id || '');
  const [selectedGarage, setSelectedGarage] = useState(garages[0]?.id || '');

  if (!isOpen || !type) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (type === 'receipt') {
      onSubmitSuccess(`Recorded receipt of ₹${Number(amount).toLocaleString('en-IN')} from ${buyerName} via ${paymentMethod}.`);
    } else if (type === 'sale') {
      onSubmitSuccess(`Sale agreement created for ${buyerName} at ₹${Number(salePrice).toLocaleString('en-IN')}.`);
    } else if (type === 'vehicle') {
      const inv = investors.find((i) => i.id === selectedInvestor);
      const newVehicle = {
        id: 'v-' + Date.now().toString(36),
        number: vehicleReg,
        model: vehicleModel,
        type: 'Stock / Investor' as const,
        garageId: selectedGarage || garages[0]?.id || 'g-1',
        person: inv ? inv.name : 'Ayaan Rahman',
        investorId: selectedInvestor || investors[0]?.id,
        status: 'Purchased' as const,
        purchase: 650000,
        totalCost: 650000,
      };
      onSubmitSuccess(`Vehicle registered: ${vehicleReg} (${vehicleModel}).`, newVehicle);
    }
    onClose();
  };

  const getTitle = () => {
    switch (type) {
      case 'receipt':
        return 'Record Buyer Receipt';
      case 'sale':
        return 'Create Vehicle Sale Agreement';
      case 'vehicle':
        return 'Register Stock / Customer Vehicle';
      default:
        return 'Quick Action';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
      <div className="bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 rounded-[28px] max-w-md w-full p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between pb-4 border-b border-gray-100 dark:border-zinc-800">
          <h3 className="text-base font-bold text-gray-950 dark:text-white">
            {getTitle()}
          </h3>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-gray-100 dark:bg-zinc-800 flex items-center justify-center text-gray-500 hover:text-black dark:hover:text-white transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {type === 'receipt' && (
            <>
              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                  Buyer Name
                </label>
                <input
                  type="text"
                  required
                  value={buyerName}
                  onChange={(e) => setBuyerName(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                  Amount Received (₹)
                </label>
                <input
                  type="number"
                  required
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                  Payment Method
                </label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)]"
                >
                  <option value="Bank transfer">Bank Transfer / IMPS</option>
                  <option value="UPI">UPI Payment</option>
                  <option value="Cheque">Cheque</option>
                  <option value="Cash">Cash Receipt</option>
                </select>
              </div>
            </>
          )}

          {type === 'sale' && (
            <>
              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                  Stock Vehicle
                </label>
                <select
                  value={vehicleReg}
                  onChange={(e) => setVehicleReg(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)]"
                >
                  <option value="KL 11 AB 4821">KL 11 AB 4821 — Jeep Wrangler</option>
                  <option value="KL 10 CK 2098">KL 10 CK 2098 — Jeep Compass</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                  Buyer Name
                </label>
                <input
                  type="text"
                  required
                  value={buyerName}
                  onChange={(e) => setBuyerName(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                  Agreed Sale Price (₹)
                </label>
                <input
                  type="number"
                  required
                  value={salePrice}
                  onChange={(e) => setSalePrice(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)]"
                />
              </div>
            </>
          )}

          {type === 'vehicle' && (
            <>
              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                  Registration Number
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. KL 10 AZ 4590"
                  value={vehicleReg}
                  onChange={(e) => setVehicleReg(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                  Make & Model
                </label>
                <input
                  type="text"
                  required
                  value={vehicleModel}
                  onChange={(e) => setVehicleModel(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                    Assigned Investor
                  </label>
                  <select
                    value={selectedInvestor}
                    onChange={(e) => setSelectedInvestor(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)]"
                  >
                    {investors.map((inv) => (
                      <option key={inv.id} value={inv.id}>
                        {inv.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                    Garage Location
                  </label>
                  <select
                    value={selectedGarage}
                    onChange={(e) => setSelectedGarage(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)]"
                  >
                    {garages.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </>
          )}

          <div className="pt-3 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-full text-xs font-bold text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-zinc-800 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-full text-xs font-bold bg-[#18181b] hover:bg-black text-white dark:bg-white dark:text-black dark:hover:bg-zinc-200 transition shadow-xs"
            >
              Confirm & Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

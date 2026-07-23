import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useWorkspaceStore = create(
  persist(
    (set) => ({
      // Paraphrase State
      paraphraseInput: "",
      paraphraseOutput: "",
      paraphraseMode: "Standard",
      paraphraseIsBatchMode: false,
      paraphraseBatchJob: null,
      paraphraseHistory: [],

      setParaphraseInput: (val) => set({ paraphraseInput: val }),
      setParaphraseOutput: (val) => set({ paraphraseOutput: val }),
      setParaphraseMode: (val) => set({ paraphraseMode: val }),
      setParaphraseIsBatchMode: (val) => set({ paraphraseIsBatchMode: val }),
      setParaphraseBatchJob: (val) => set({ paraphraseBatchJob: val }),
      setParaphraseHistory: (val) => set({ paraphraseHistory: val }),

      // Translate State
      translateInput: "",
      translateOutput: "",
      translateFromLang: "English",
      translateToLang: "Urdu",
      translateIsBatchMode: false,
      translateBatchJob: null,

      setTranslateInput: (val) => set({ translateInput: val }),
      setTranslateOutput: (val) => set({ translateOutput: val }),
      setTranslateFromLang: (val) => set({ translateFromLang: val }),
      setTranslateToLang: (val) => set({ translateToLang: val }),
      setTranslateIsBatchMode: (val) => set({ translateIsBatchMode: val }),
      setTranslateBatchJob: (val) => set({ translateBatchJob: val }),

      // Grammar State
      grammarInput: "",
      grammarOutput: "",
      setGrammarInput: (val) => set({ grammarInput: val }),
      setGrammarOutput: (val) => set({ grammarOutput: val }),

      // OCR State
      ocrInput: "",
      ocrOutput: "",
      setOcrInput: (val) => set({ ocrInput: val }),
      setOcrOutput: (val) => set({ ocrOutput: val }),

      // Documents State
      documentsInputType: "text",
      documentsTaskType: "paraphrase",
      documentsText: "",
      documentsLanguage: "urdu",
      documentsActiveJobs: [],

      setDocumentsInputType: (val) => set({ documentsInputType: val }),
      setDocumentsTaskType: (val) => set({ documentsTaskType: val }),
      setDocumentsText: (val) => set({ documentsText: val }),
      setDocumentsLanguage: (val) => set({ documentsLanguage: val }),
      setDocumentsActiveJobs: (val) => set((state) => ({ documentsActiveJobs: typeof val === "function" ? val(state.documentsActiveJobs) : val })),
    }),
    {
      name: "rephrasia-workspace-storage", // unique name for localStorage key
      partialize: (state) => {
        // Exclude transient state or large data that shouldn't be saved
        // Note: files (Blobs) cannot be JSON serialized anyway, but we didn't add them here.
        return state;
      },
    }
  )
);

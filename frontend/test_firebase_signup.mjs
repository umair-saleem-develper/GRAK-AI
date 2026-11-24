import { initializeApp } from 'firebase/app';
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "grak-ai.firebaseapp.com",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "grak-ai"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

async function run() {
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, "testuser99@example.com", "Password123!");
    console.log("Signup success!");
    const token = await userCredential.user.getIdToken();
    console.log("Token:", token.substring(0, 30) + "...");
  } catch (e) {
    if (e.code === 'auth/email-already-in-use') {
       console.log("User exists, trying login...");
       const userCredential = await signInWithEmailAndPassword(auth, "testuser99@example.com", "Password123!");
       console.log("Login success!");
       const token = await userCredential.user.getIdToken();
       console.log("Token:", token.substring(0, 30) + "...");
    } else {
       console.error(e);
    }
  }
  process.exit(0);
}
run();

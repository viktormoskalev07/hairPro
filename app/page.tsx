import WigEditor from '../components/WigEditor';

export default function Home() {
  return (
    <main className="min-h-screen p-4 flex flex-col items-center">
      <h1 className="text-3xl font-bold mb-4">Try On Wigs</h1>
      <p className="text-gray-600 mb-8 text-center max-w-lg">
        Take a photo or upload one, then choose a wig to place on your head. 
        Everything happens securely on your own device!
      </p>
      <WigEditor />
    </main>
  );
}

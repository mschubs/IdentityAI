import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ArrowRight, Check, X } from "lucide-react";
import { useState, useEffect, useRef } from "react";

const identityData = {
  observed: {
    profileImage: "/images/OldDerek.jpeg",
    name: "John Doe",
    idNumber: "123456789",
    dateOfBirth: "01/01/1990",
    expiryDate: "01/01/2025",
    nationality: "United States",
    gender: "Male",
  },
  online: [
    {
      profileImage: "/images/NewDerek.jpeg",
      name: "REF123",
      idNumber: "123456789",
      dateOfBirth: "01/01/2001",
      expiryDate: "01/03/2025",
      nationality: "United States",
      gender: "Male",
    },
    {
      profileImage: "/images/michaelID.jpeg",
      name: "REF123",
      idNumber: "123456789",
      dateOfBirth: "01/01/2001",
      expiryDate: "01/03/2025",
      nationality: "United States",
      gender: "Male",
    },
    {
      profileImage: "/images/nandan.jpeg",
      name: "REF123",
      idNumber: "123456789",
      dateOfBirth: "01/01/1990",
      expiryDate: "01/01/2025",
      nationality: "United States",
      gender: "Female",
    },
  ],
};

function App() {
  const [faceSimilarityResults, setFaceSimilarityResults] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [apiCallsInProgress, setApiCallsInProgress] = useState(false);
  const mountedRef = useRef(false);

  useEffect(() => {
    // Skip the first render in development
    if (!mountedRef.current) {
      mountedRef.current = true;
      return;
    }

    const checkFaceSimilarity = async () => {
      if (currentIndex >= identityData.online.length || apiCallsInProgress) {
        setIsLoading(false);
        return;
      }

      setApiCallsInProgress(true);

      try {
        const onlineData = identityData.online[currentIndex];
        console.log(`Making API call for index ${currentIndex}`);

        const response = await fetch("http://localhost:8000/compare-faces", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            known_image: identityData.observed.profileImage,
            unknown_image: onlineData.profileImage,
          }),
        });
        const data = await response.json();

        setFaceSimilarityResults((prev) => [...prev, data.result]);
        setApiCallsInProgress(false);
        setCurrentIndex((prev) => prev + 1);
      } catch (error) {
        console.error("Error comparing faces:", error);
        setApiCallsInProgress(false);
        setCurrentIndex((prev) => prev + 1);
      }
    };

    checkFaceSimilarity();
  }, [currentIndex, apiCallsInProgress]);

  return (
    <div className="min-h-screen h-full w-full bg-gray-100">
      <div className="fixed left-8 top-1/2 -translate-y-1/2">
        <div className="flex items-center">
          <Card className="w-[400px]">
            <h1 className="text-2xl font-bold text-center py-2">
              Observed ID Data
            </h1>
            <CardHeader className="flex flex-row items-center gap-4">
              <Avatar className="h-20 w-20 rounded-md">
                <AvatarImage
                  src={identityData.observed.profileImage}
                  alt="Profile Picture"
                  className="object-cover"
                />
                <AvatarFallback>JD</AvatarFallback>
              </Avatar>
              <div>
                <h2 className="text-2xl font-bold">
                  {identityData.observed.name}
                </h2>
                <p className="text-gray-500">
                  ID: {identityData.observed.idNumber}
                </p>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-2">
                <div>
                  <p className="text-sm text-gray-500">Date of Birth</p>
                  <p className="font-medium">
                    {identityData.observed.dateOfBirth}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Expiry Date</p>
                  <p className="font-medium">
                    {identityData.observed.expiryDate}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Nationality</p>
                  <p className="font-medium">
                    {identityData.observed.nationality}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Gender</p>
                  <p className="font-medium">{identityData.observed.gender}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <ArrowRight className="w-8 h-8 text-gray-400 pl-2" />
        </div>
      </div>

      <div className="ml-[450px] h-screen overflow-y-auto flex items-center">
        <div className="flex items-center gap-6 px-6">
          {identityData.online.map((onlineData, index) => (
            <Card
              key={index}
              className={`w-[400px] ${
                index > currentIndex ? "opacity-50" : ""
              }`}
            >
              <h1 className="text-2xl font-bold text-center py-2">
                Found Online Information
              </h1>
              <CardHeader className="flex flex-row items-center gap-4">
                <Avatar className="h-20 w-20 rounded-md">
                  <AvatarImage
                    src={onlineData.profileImage}
                    alt="Secondary Profile"
                    className="object-cover"
                  />
                  <AvatarFallback>SD</AvatarFallback>
                </Avatar>
                <div>
                  <h2 className="text-2xl font-bold flex items-center gap-2">
                    {index === currentIndex ? (
                      <span className="text-gray-600">
                        Checking face similarity...
                      </span>
                    ) : index > currentIndex ? (
                      <span className="text-gray-400">Waiting...</span>
                    ) : faceSimilarityResults[index] ? (
                      <>
                        <span className="text-green-600">
                          Face similarity passed
                        </span>
                        <Check className="w-5 h-5 text-green-500" />
                      </>
                    ) : (
                      <>
                        <span className="text-red-600">
                          Face similarity failed
                        </span>
                        <X className="w-5 h-5 text-red-500" />
                      </>
                    )}
                  </h2>
                  <p className="text-gray-500">ID: {onlineData.idNumber}</p>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Date of Birth</p>
                      <p
                        className={`font-medium ${
                          onlineData.dateOfBirth ===
                          identityData.observed.dateOfBirth
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {onlineData.dateOfBirth}
                      </p>
                    </div>
                    {onlineData.dateOfBirth ===
                    identityData.observed.dateOfBirth ? (
                      <Check className="w-5 h-5 text-green-500" />
                    ) : (
                      <X className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Expiry Date</p>
                      <p
                        className={`font-medium ${
                          onlineData.expiryDate ===
                          identityData.observed.expiryDate
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {onlineData.expiryDate}
                      </p>
                    </div>
                    {onlineData.expiryDate ===
                    identityData.observed.expiryDate ? (
                      <Check className="w-5 h-5 text-green-500" />
                    ) : (
                      <X className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Nationality</p>
                      <p
                        className={`font-medium ${
                          onlineData.nationality ===
                          identityData.observed.nationality
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {onlineData.nationality}
                      </p>
                    </div>
                    {onlineData.nationality ===
                    identityData.observed.nationality ? (
                      <Check className="w-5 h-5 text-green-500" />
                    ) : (
                      <X className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Gender</p>
                      <p
                        className={`font-medium ${
                          onlineData.gender === identityData.observed.gender
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {onlineData.gender}
                      </p>
                    </div>
                    {onlineData.gender === identityData.observed.gender ? (
                      <Check className="w-5 h-5 text-green-500" />
                    ) : (
                      <X className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;

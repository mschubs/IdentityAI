import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ArrowRight, Check, X } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { PieChart, Pie, Cell } from "recharts";

const previousIDs = [
  {
    profileImage: "/images/OldDerek.jpeg",
    name: "John Doe",
    idNumber: "123456789",
  },
];

const identityData = {
  observed: {
    profileImage: "/images/OldDerek.jpeg",
    name: "Nandan M Srikrishna",
    "address-line-1": "794 BRODHEAD DR",
    "address-line-2": "AURORA, IL 60504",
    dateOfBirth: "10/12/2001",
    expiryDate: "10/12/2026",
    nationality: "USA",
    gender: "M",
  },
  online: [
    {
      profileImage: "/images/NewDerek.jpeg",
      name: "REF123",
      "address-line-1": "794 Brodhead Dr",
      "address-line-2": "Aurora, IL 60504",
      age: "23",
      expiryDate: "01/03/2025",
      nationality: "USA",
      gender: "M",
    },
    {
      profileImage: "/images/michaelID.jpeg",
      name: "REF123",
      "address-line-1": "456 Oak St",
      "address-line-2": "City ST 12345",
      age: "22",
      expiryDate: "01/03/2025",
      nationality: "USA",
      gender: "M",
    },
    {
      profileImage: "/images/nandan.jpeg",
      name: "REF123",
      "address-line-1": "789 Pine St",
      "address-line-2": "City ST 12345",
      age: "24",
      expiryDate: "01/01/2025",
      nationality: "USA",
      gender: "F",
    },
    {
      profileImage: "/images/michaelID.jpeg",
      name: "REF123",
      "address-line-1": "321 Elm St",
      "address-line-2": "City ST 12345",
      age: "24",
      expiryDate: "01/03/2025",
      nationality: "USA",
      gender: "M",
    },
    {
      profileImage: "/images/nandan.jpeg",
      name: "REF123",
      "address-line-1": "654 Maple St",
      "address-line-2": "City ST 12345",
      age: "24",
      expiryDate: "01/01/2025",
      nationality: "USA",
      gender: "F",
    },
  ],
};

const calculateAge = (dateOfBirth) => {
  const [month, day, year] = dateOfBirth.split("/");
  const birthDate = new Date(year, month - 1, day);
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();

  if (
    monthDiff < 0 ||
    (monthDiff === 0 && today.getDate() < birthDate.getDate())
  ) {
    age--;
  }

  return age;
};

function App() {
  const [faceSimilarityResults, setFaceSimilarityResults] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [apiCallsInProgress, setApiCallsInProgress] = useState(false);
  const [identityDataState, setIdentityDataState] = useState(identityData);
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
        console.log(data.result);

        setFaceSimilarityResults((prev) => [
          ...prev,
          [parseInt(data.result) > 50 ? true : false, data.result],
        ]);
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
    <div className="min-h-screen h-full w-full bg-gray-100 dark:bg-gray-900 overflow-x-hidden relative">
      <div className="container mx-auto p-8">
        <div className="flex flex-col md:flex-row gap-8">
          <div className="flex-shrink-0">
            <div className="flex flex-col">
              <Label className="text-lg font-semibold mb-4 sticky top-0 bg-gray-100 dark:bg-gray-900 py-2 z-10">
                Observed ID Data
              </Label>
              <div className="flex items-center">
                <Card className="w-[340px] border-2 hover:border-primary/50 transition-colors">
                  <CardHeader className="flex flex-row items-center gap-4">
                    <Avatar className="h-24 w-20 rounded-md">
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
                      {/* <p className="text-gray-500">
                        ID: {identityData.observed.idNumber}
                      </p> */}
                    </div>
                  </CardHeader>
                  <Separator className="my-2" />
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 gap-2">
                      <div>
                        <p className="text-sm text-gray-500">Address</p>
                        <div className="font-medium">
                          <p>{identityData.observed["address-line-1"]}</p>
                          <p>{identityData.observed["address-line-2"]}</p>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Date of Birth</p>
                        <p className="font-medium">
                          {identityData.observed.dateOfBirth}
                          <ArrowRight className="inline-block w-4 h-4 mx-1" />
                          Calculated Age:{" "}
                          {calculateAge(identityData.observed.dateOfBirth)}
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
                        <p className="font-medium">
                          {identityData.observed.gender}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <ArrowRight className="w-8 h-8 text-primary/50 pl-2" />
              </div>
            </div>
          </div>

          <ScrollArea className="w-full">
            <div className="flex flex-col">
              <Label className="text-lg font-semibold mb-4 sticky top-0 bg-gray-100 dark:bg-gray-900 py-2 z-10">
                Found Online Information
              </Label>
              <div className="flex gap-6 pb-4">
                {identityData.online.map((onlineData, index) => (
                  <Card
                    key={index}
                    className={`w-[340px] flex-shrink-0 border-2 transition-all duration-200 ${
                      index > currentIndex
                        ? "opacity-50"
                        : "hover:border-primary/50"
                    }`}
                  >
                    <CardHeader className="flex flex-row items-center gap-4">
                      <Avatar className="h-24 w-20 rounded-md">
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
                          ) : faceSimilarityResults[index] === undefined ? (
                            <>
                              <span className="text-orange-400">
                                Server is not running
                              </span>
                            </>
                          ) : (
                            <div className="flex items-center gap-2">
                              <span
                                className={
                                  faceSimilarityResults[index][0]
                                    ? "text-green-600"
                                    : "text-red-600"
                                }
                              >
                                {faceSimilarityResults[index][0]
                                  ? "Face similarity passed"
                                  : "Face similarity failed"}
                              </span>
                              {/* {faceSimilarityResults[index][0] ? (
                                <Check className="w-5 h-5 text-green-500" />
                              ) : (
                                <X className="w-5 h-5 text-red-500" />
                              )} */}
                              <div className="flex flex-col">
                                <PieChart
                                  className="mr-2"
                                  width={50}
                                  height={50}
                                >
                                  <Pie
                                    data={[
                                      {
                                        value: faceSimilarityResults[index][1],
                                      },
                                      {
                                        value:
                                          100 - faceSimilarityResults[index][1],
                                      },
                                    ]}
                                    cx={25}
                                    cy={20}
                                    innerRadius={15}
                                    outerRadius={20}
                                    startAngle={90}
                                    endAngle={-270}
                                    dataKey="value"
                                    // animationBegin={0}
                                    // animationDuration={1000}
                                    // isAnimationActive={true}
                                  >
                                    <Cell
                                      fill={
                                        faceSimilarityResults[index][0]
                                          ? "#22c55e"
                                          : "#ef4444"
                                      }
                                    />
                                    <Cell fill="#e5e7eb" />
                                  </Pie>
                                </PieChart>
                                <span className="mt-2 text-sm">
                                  {faceSimilarityResults[index][1].toFixed(2)}%
                                </span>
                              </div>
                            </div>
                          )}
                        </h2>
                        {/* <p className="text-gray-500">ID: {onlineData.idNumber}</p> */}
                      </div>
                    </CardHeader>
                    <Separator className="my-2" />
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 gap-2">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-gray-500">Address</p>
                            <div
                              className={`font-medium ${
                                onlineData["address-line-1"].toLowerCase() ===
                                  identityData.observed[
                                    "address-line-1"
                                  ].toLowerCase() &&
                                onlineData["address-line-2"].toLowerCase() ===
                                  identityData.observed[
                                    "address-line-2"
                                  ].toLowerCase()
                                  ? "text-green-600"
                                  : "text-red-600"
                              }`}
                            >
                              <p>{onlineData["address-line-1"]}</p>
                              <p>{onlineData["address-line-2"]}</p>
                            </div>
                          </div>
                          {onlineData["address-line-1"].toLowerCase() ===
                            identityData.observed[
                              "address-line-1"
                            ].toLowerCase() &&
                          onlineData["address-line-2"].toLowerCase() ===
                            identityData.observed[
                              "address-line-2"
                            ].toLowerCase() ? (
                            <Check className="w-5 h-5 text-green-500" />
                          ) : (
                            <X className="w-5 h-5 text-red-500" />
                          )}
                        </div>
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-gray-500">Age</p>
                            <p
                              className={`font-medium ${
                                parseInt(onlineData.age) ===
                                parseInt(
                                  calculateAge(
                                    identityData.observed.dateOfBirth
                                  )
                                )
                                  ? "text-green-600"
                                  : "text-red-600"
                              }`}
                            >
                              {onlineData.age}
                            </p>
                          </div>
                          {parseInt(onlineData.age) ===
                          parseInt(
                            calculateAge(identityData.observed.dateOfBirth)
                          ) ? (
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
                                onlineData.gender ===
                                identityData.observed.gender
                                  ? "text-green-600"
                                  : "text-red-600"
                              }`}
                            >
                              {onlineData.gender}
                            </p>
                          </div>
                          {onlineData.gender ===
                          identityData.observed.gender ? (
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
              <ScrollBar orientation="horizontal" />
            </div>
          </ScrollArea>
        </div>
      </div>

      <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2">
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="outline">Change ID</Button>
          </DialogTrigger>
          <DialogContent className="max-w-[800px]">
            <DialogHeader>
              <DialogTitle>Change ID</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4">
              <div>
                <Label>Previous IDs</Label>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

export default App;

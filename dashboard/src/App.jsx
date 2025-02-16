import {
  Card,
  CardContent,
  CardHeader,
  CardFooter,
} from "@/components/ui/card";
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
import data from "./data.json";

function App() {
  const [faceSimilarityResult, setFaceSimilarityResult] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentIDIndex, setCurrentIDIndex] = useState(0);
  const [currentIndex, setCurrentIndex] = useState(0);
  const mountedRef = useRef(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [allData, setAllData] = useState(data.allData);
  const [previousIDs, setPreviousIDs] = useState([]);

  useEffect(() => {
    setPreviousIDs(
      data.allData.map((data, index) => ({
        index,
        profileImage: data.observed.profileImage,
        name: data.observed.name,
        date_created: "2024-01-01",
      }))
    );
  }, [data.allData]);

  useEffect(() => {
    const loadData = async () => {
      try {
        setAllData(data.allData);
      } catch (error) {
        console.error("Error loading data:", error);
        setError("Error loading data");
      }
    };

    loadData();
  }, []);

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

  const getMatchScore = (data, observedData) => {
    let score = 0;
    // Name match
    if (data.name.toLowerCase() === observedData.name.toLowerCase()) {
      score += 1;
    }
    // Address match (both lines)
    if (
      data["address-line-1"].toLowerCase() ===
        observedData["address-line-1"].toLowerCase() &&
      data["address-line-2"].toLowerCase() ===
        observedData["address-line-2"].toLowerCase()
    ) {
      score += 1;
    }
    // Age match
    if (
      parseInt(data.age) === parseInt(calculateAge(observedData.dateOfBirth))
    ) {
      score += 1;
    }
    return score;
  };

  const identityData =
    allData.length > 0
      ? {
          ...allData[currentIDIndex],
          online: [...allData[currentIDIndex].online].sort((a, b) => {
            return (
              getMatchScore(b, allData[currentIDIndex].observed) -
              getMatchScore(a, allData[currentIDIndex].observed)
            );
          }),
        }
      : null;

  useEffect(() => {
    if (allData.length > 0) {
      setCurrentIndex(allData[currentIDIndex].online.length - 1);
    }
  }, [allData, currentIDIndex]);

  useEffect(() => {
    console.log("Effect running with currentIDIndex:", currentIDIndex);
    console.log("mountedRef.current:", mountedRef.current);

    if (!mountedRef.current) {
      mountedRef.current = true;
      return;
    }

    if (!identityData?.observed?.profileImage || !identityData?.IRL_image) {
      setError("Missing image data");
      setIsLoading(false);
      return;
    }

    const checkFaceSimilarity = async () => {
      try {
        const response = await fetch("http://localhost:8000/compare-faces", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            known_image: identityData.observed.profileImage,
            unknown_image: identityData.observed.faceImage,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (!data || !data.result) {
          throw new Error("Invalid response data");
        }

        console.log("Face comparison result:", data.result);
        setError(null);
        setFaceSimilarityResult([
          parseInt(data.result) > 50 ? true : false,
          parseFloat(data.result),
        ]);
      } catch (error) {
        console.error("Error comparing faces:", error);
        setError("Server not responding");
        setFaceSimilarityResult(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkFaceSimilarity();
  }, [currentIDIndex]);

  const handleIdChange = (index) => {
    if (index !== currentIDIndex) {
      setCurrentIDIndex(index);
      setCurrentIndex(allData[index].online.length - 1);
      setIsLoading(true);
      setFaceSimilarityResult(null);
      setDialogOpen(false);
    } else {
      setDialogOpen(false);
    }
  };

  return (
    <div className="h-screen w-full bg-gray-100 dark:bg-gray-900 overflow-hidden relative">
      <div className="container mx-auto p-8 h-full overflow-y-auto overflow-x-hidden">
        <div className="flex flex-col md:flex-row gap-8">
          <div className="flex-shrink-0">
            <div className="flex flex-col">
              <Label className="text-lg font-semibold mb-4 bg-gray-100 dark:bg-gray-900 py-2 z-10">
                Observed ID Data
              </Label>
              <div className="flex items-center">
                <Card className="w-[340px] border-2 hover:border-primary/50 transition-colors">
                  <CardHeader className="flex flex-row items-center gap-4">
                    <div>
                      <h2 className="text-2xl font-bold">
                        {identityData?.observed.name}
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
                          <p>{identityData?.observed["address-line-1"]}</p>
                          <p>{identityData?.observed["address-line-2"]}</p>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Date of Birth</p>
                        <p className="font-medium">
                          {identityData?.observed.dateOfBirth}
                          <ArrowRight className="inline-block w-4 h-4 mx-1" />
                          Calculated Age:{" "}
                          {calculateAge(identityData?.observed.dateOfBirth)}
                        </p>
                      </div>
                      {/* <div>
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
                      </div> */}
                    </div>
                  </CardContent>
                </Card>
                <div className="h-[400px] mx-4 border-l-2 border-gray-200" />
              </div>
            </div>
          </div>
          <div className="flex flex-col w-full overflow-x-hidden">
            <Label className="text-lg font-semibold mb-4 sticky top-0 bg-gray-100 dark:bg-gray-900 py-2">
              Found Online Information
            </Label>
            <div className="flex items-center h-full">
              <ScrollArea className="w-full">
                <div className="flex gap-6 max-w-[100vw]">
                  {identityData?.online.map((onlineData, index) => (
                    <Card
                      key={index}
                      className={`w-[340px] flex-shrink-0 border-2 transition-all duration-200 relative ${
                        index > currentIndex
                          ? "opacity-50"
                          : index === 0
                          ? "border-green-500 hover:border-green-600"
                          : "hover:border-primary/50"
                      }`}
                    >
                      {index === 0 && (
                        <div className="absolute top-50 left-1/2 transform -translate-x-1/2 bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium z-10">
                          Most likely match
                        </div>
                      )}
                      <CardHeader className="flex flex-row items-center gap-4">
                        <div>
                          <h2
                            className={`text-2xl font-bold ${
                              onlineData.name.toLowerCase() ===
                              identityData.observed.name.toLowerCase()
                                ? "text-green-600"
                                : "text-red-600"
                            }`}
                          >
                            {onlineData.name}
                          </h2>
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
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                <ScrollBar orientation="horizontal" />
              </ScrollArea>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-6 mt-8">
          <Card className="p-6 max-w-[50%] overflow-hidden">
            <CardHeader className="pb-4">
              <h3 className="text-xl font-semibold">Face Comparison</h3>
            </CardHeader>
            <CardContent>
              <ScrollArea className="w-full">
                <div className="flex items-center gap-6 min-w-min">
                  <Card className="p-4">
                    <CardContent className="flex items-center justify-center">
                      <Avatar className="h-32 w-28 rounded-md">
                        <AvatarImage
                          src={identityData?.observed.profileImage}
                          alt="Profile Picture"
                          className="object-cover"
                        />
                        <AvatarFallback>JD</AvatarFallback>
                      </Avatar>
                    </CardContent>
                    <CardFooter className="pb-2">
                      <h3 className="text-lg font-semibold text-center w-full">
                        Observed ID Photo
                      </h3>
                    </CardFooter>
                  </Card>
                  <ArrowRight className="w-8 h-8 text-primary/50 flex-shrink-0" />
                  <Card className="p-4">
                    <CardContent className="flex items-center justify-center">
                      <Avatar className="h-32 w-28 rounded-md">
                        <AvatarImage
                          src={identityData.observed.faceImage}
                          alt="Secondary Profile"
                          className="object-cover"
                        />
                        <AvatarFallback>SD</AvatarFallback>
                      </Avatar>
                    </CardContent>
                    <CardFooter className="pb-2">
                      <h3 className="text-lg font-semibold text-center w-full">
                        Live Photo Comparison
                      </h3>
                    </CardFooter>
                  </Card>
                  <div className="flex flex-col items-center min-w-[80px] flex-shrink-0">
                    {error ? (
                      <span className="text-orange-400 text-center">
                        {error}
                      </span>
                    ) : isLoading ? (
                      <span className="text-gray-500">Loading...</span>
                    ) : faceSimilarityResult ? (
                      <div className="flex flex-col">
                        <PieChart width={80} height={80}>
                          <Pie
                            data={[
                              { value: faceSimilarityResult[1] || 0 },
                              { value: 100 - (faceSimilarityResult[1] || 0) },
                            ]}
                            cx={40}
                            cy={40}
                            innerRadius={25}
                            outerRadius={35}
                            startAngle={90}
                            endAngle={-270}
                            dataKey="value"
                          >
                            <Cell
                              fill={
                                faceSimilarityResult[0] ? "#22c55e" : "#ef4444"
                              }
                            />
                            <Cell fill="#e5e7eb" />
                          </Pie>
                        </PieChart>
                        <span className="mt-2 font-medium text-center">
                          {(faceSimilarityResult[1] || 0).toFixed(2)}% Match
                        </span>
                      </div>
                    ) : (
                      <span className="text-gray-500">No data</span>
                    )}
                  </div>
                </div>
                <ScrollBar orientation="horizontal" />
              </ScrollArea>
            </CardContent>
          </Card>

          <Card className="p-6 flex-1">
            <CardHeader className="pb-4">
              <h3 className="text-xl font-semibold">Additional Information</h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Label className="text-sm text-gray-500">Found Web Links</Label>
                <ScrollArea className="h-[220px] pr-4">
                  <div className="space-y-2">
                    {identityData?.web_links.map((link, index) => (
                      <Card
                        key={index}
                        className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          {/* <Avatar className="h-6 w-6">
                            <AvatarImage
                              src={link.favicon}
                              alt={link.platform}
                            />
                            <AvatarFallback>{link.platform[0]}</AvatarFallback>
                          </Avatar> */}
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-start">
                              <div>
                                <h4 className="font-medium text-sm truncate">
                                  {link.title}
                                </h4>
                                <a
                                  href={link.url}
                                  className="text-xs text-blue-600 hover:underline truncate block"
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  {link.url}
                                </a>
                              </div>
                              <Button
                                variant="outline"
                                size="sm"
                                className="text-xs"
                                onClick={() => window.open(link.url, "_blank")}
                              >
                                Visit Site
                              </Button>
                            </div>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                  <ScrollBar />
                </ScrollArea>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="p-6 mt-6">
          <CardHeader className="pb-4">
            <h3 className="text-xl font-semibold">Automated Bio</h3>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {identityData?.bio}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2">
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
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
                <div className="flex flex-wrap flex-col gap-2">
                  {previousIDs.map((id) => (
                    <Button
                      key={id.index}
                      variant="outline"
                      className="flex items-center gap-3 h-auto p-2"
                      onClick={() => handleIdChange(id.index)}
                    >
                      <Avatar className="h-8 w-8 rounded-md">
                        <AvatarImage
                          src={id.profileImage}
                          alt={id.name}
                          className="object-cover "
                        />
                        <AvatarFallback>{id.name.charAt(0)}</AvatarFallback>
                      </Avatar>
                      <div className="flex flex-col items-start">
                        <span className="font-medium">{id.name}</span>
                      </div>
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

export default App;

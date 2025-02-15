import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ArrowRight } from "lucide-react";

const identityData = {
  observed: {
    profileImage: "https://github.com/shadcn.png",
    name: "John Doe",
    idNumber: "123456789",
    dateOfBirth: "01/01/1990",
    expiryDate: "01/01/2025",
    nationality: "United States",
    gender: "Male",
  },
  online: [
    {
      profileImage: "https://github.com/shadcn.png",
      reference: "REF123",
      issueDate: "01/01/2020",
      issuingAuthority: "Department of State",
      documentType: "Passport",
      status: "Active",
    },
    {
      profileImage: "https://github.com/shadcn.png",
      reference: "REF123",
      issueDate: "01/01/2020",
      issuingAuthority: "Department of State",
      documentType: "Passport",
      status: "Active",
    },
    {
      profileImage: "https://github.com/shadcn.png",
      reference: "REF123",
      issueDate: "01/01/2020",
      issuingAuthority: "Department of State",
      documentType: "Passport",
      status: "Active",
    },
    {
      profileImage: "https://github.com/shadcn.png",
      reference: "REF123",
      issueDate: "01/01/2020",
      issuingAuthority: "Department of State",
      documentType: "Passport",
      status: "Active",
    },
    {
      profileImage: "https://github.com/shadcn.png",
      reference: "REF123",
      issueDate: "01/01/2020",
      issuingAuthority: "Department of State",
      documentType: "Passport",
      status: "Active",
    },
    {
      profileImage: "https://github.com/shadcn.png",
      reference: "REF123",
      issueDate: "01/01/2020",
      issuingAuthority: "Department of State",
      documentType: "Passport",
      status: "Active",
    },
  ],
};

function App() {
  return (
    <div className="min-h-screen h-full w-full bg-gray-100">
      <div className="fixed left-8 top-1/2 -translate-y-1/2">
        <Card className="w-[400px]">
          <h1 className="text-2xl font-bold text-center py-2">
            Observed ID Data
          </h1>
          <CardHeader className="flex flex-row items-center gap-4">
            <Avatar className="h-20 w-20 rounded-md">
              <AvatarImage
                src={identityData.observed.profileImage}
                alt="Profile Picture"
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
      </div>

      <div className="ml-[450px] h-screen overflow-y-auto flex items-center">
        <div className="flex items-center gap-6 px-6">
          <ArrowRight className="w-8 h-8 text-gray-400 sticky left-0" />
          {identityData.online.map((onlineData, index) => (
            <Card key={index} className="w-[400px]">
              <h1 className="text-2xl font-bold text-center py-2">
                Found Online Information
              </h1>
              <CardHeader className="flex flex-row items-center gap-4">
                <Avatar className="h-20 w-20 rounded-md">
                  <AvatarImage
                    src={onlineData.profileImage}
                    alt="Secondary Profile"
                  />
                  <AvatarFallback>SD</AvatarFallback>
                </Avatar>
                <div>
                  <h2 className="text-2xl font-bold">Secondary Data</h2>
                  <p className="text-gray-500">
                    Reference: {onlineData.reference}
                  </p>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-2">
                  <div>
                    <p className="text-sm text-gray-500">Issue Date</p>
                    <p className="font-medium">{onlineData.issueDate}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Issuing Authority</p>
                    <p className="font-medium">{onlineData.issuingAuthority}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Document Type</p>
                    <p className="font-medium">{onlineData.documentType}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Status</p>
                    <p className="font-medium">{onlineData.status}</p>
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
